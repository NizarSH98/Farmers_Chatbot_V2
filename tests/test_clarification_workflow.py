from __future__ import annotations

from typing import Any, ClassVar

import pytest
from pydantic import ValidationError

from farmers_chatbot.assistant_pipeline import AssistantEngine
from farmers_chatbot.clarification import (
    ClarificationWorkflow,
    StructuredRequestAnalysis,
)
from farmers_chatbot.trusted_sources import (
    TrustedSourceClient,
    load_live_source_registry,
    url_is_trusted,
)


def analysis_data(*, needs: bool, language: str = "english") -> dict[str, Any]:
    arabic = language == "arabic"
    return {
        "intent": "farm planning",
        "decision": "choose a practical plan",
        "domain": "agriculture",
        "risk": "medium",
        "currentness": "stable",
        "location": None,
        "missing_fields": ["crop"] if needs else [],
        "needs_clarification": needs,
        "clarification_question": (
            "\u0645\u0627 \u0627\u0644\u0645\u062d\u0635\u0648\u0644 \u0627\u0644\u0630\u064a \u062a\u0632\u0631\u0639\u0647\u061f"
            if arabic
            else "Which crop do you grow?"
        )
        if needs
        else None,
        "clarification_options": (
            [
                "\u0628\u0637\u0627\u0637\u0627",
                "\u0628\u0646\u062f\u0648\u0631\u0629",
                "\u0645\u062d\u0635\u0648\u0644 \u0622\u062e\u0631",
            ]
            if arabic
            else ["Potato", "Tomato", "Another crop"]
        )
        if needs
        else [],
        # Left empty on purpose: the model validator synthesizes the typed
        # question from clarification_question/clarification_options.
        "clarification_questions": [],
        "retrieval_queries": ["farm planning"],
        "evidence_requirements": [],
        "output_shape": "practical steps",
        "assumptions": [],
    }


def test_arabic_choices_reject_punctuation_only_model_output() -> None:
    value = analysis_data(needs=True, language="arabic")
    value["clarification_options"] = ["\u3001", "...", "\u061f\u061f\u061f"]
    with pytest.raises(ValidationError, match="punctuation-only"):
        StructuredRequestAnalysis.model_validate(value, context={"language": "arabic"})


def test_choices_must_match_the_users_writing_system() -> None:
    value = analysis_data(needs=True, language="arabic")
    value["clarification_options"] = ["Potato", "Tomato", "Other"]
    with pytest.raises(ValidationError, match="writing system"):
        StructuredRequestAnalysis.model_validate(value, context={"language": "arabic"})


@pytest.mark.asyncio
async def test_workflow_resumes_and_stops_after_three_rounds() -> None:
    calls: list[str] = []

    async def planner(state: dict[str, Any]) -> StructuredRequestAnalysis:
        calls.append(str(state["effective_text"]))
        return StructuredRequestAnalysis.model_validate(
            analysis_data(needs=True), context={"language": "english"}
        )

    workflow = ClarificationWorkflow("", planner)
    common = {
        "actor_id": "user-1",
        "conversation_id": "conversation-1",
        "language": "english",
        "mode": "standard",
        "clarification_style": "auto",
        "history": [],
    }
    first = await workflow.advance(text="Help with my farm", **common)
    second = await workflow.advance(text="Potato", **common)
    third = await workflow.advance(text="Akkar", **common)
    final = await workflow.advance(text="Two hectares", **common)
    assert first.pending and first.interaction["round"] == 1
    assert second.pending and second.interaction["round"] == 2
    assert third.pending and third.interaction["round"] == 3
    assert not final.pending
    assert all(
        value in final.effective_text for value in ("Potato", "Akkar", "Two hectares")
    )
    assert "clarification-round limit" in final.analysis["assumptions"][0]
    assert len(calls) == 4


def test_fallback_clarification_confusion_matrix() -> None:
    cases = [
        ("tp", "Help", "english", True),
        ("tp", "What should I do?", "english", True),
        ("tp", "\u0633\u0627\u0639\u062f\u0646\u064a", "arabic", True),
        ("tp", "\u0634\u0648 \u0627\u0639\u0645\u0644\u061f", "arabic", True),
        ("false_negative_guard", "Plant sick", "english", True),
        ("false_negative_guard", "Help with potatoes", "english", True),
        (
            "false_negative_guard",
            "\u0627\u0644\u0646\u0628\u0627\u062a \u0645\u0631\u064a\u0636",
            "arabic",
            True,
        ),
        (
            "false_negative_guard",
            "\u0645\u0633\u0627\u0639\u062f\u0629 \u0628\u0627\u0644\u0628\u0637\u0627\u0637\u0627",
            "arabic",
            True,
        ),
        (
            "tn",
            "Explain integrated pest management for a potato farm",
            "english",
            False,
        ),
        ("tn", "Give me a potato irrigation checklist for Akkar", "english", False),
        (
            "tn",
            "\u0627\u0634\u0631\u062d \u0627\u0644\u0625\u062f\u0627\u0631\u0629 \u0627\u0644\u0645\u062a\u0643\u0627\u0645\u0644\u0629 \u0644\u0644\u0622\u0641\u0627\u062a \u0641\u064a \u062d\u0642\u0644 \u0627\u0644\u0628\u0637\u0627\u0637\u0627",
            "arabic",
            False,
        ),
        (
            "tn",
            "\u0627\u0639\u0637\u0646\u064a \u0642\u0627\u0626\u0645\u0629 \u0631\u064a \u0644\u0644\u0628\u0637\u0627\u0637\u0627 \u0641\u064a \u0639\u0643\u0627\u0631",
            "arabic",
            False,
        ),
        ("false_positive_guard", "Potato price today?", "english", False),
        ("false_positive_guard", "Define IPM", "english", False),
        (
            "false_positive_guard",
            "\u0633\u0639\u0631 \u0627\u0644\u0628\u0637\u0627\u0637\u0627 \u0627\u0644\u064a\u0648\u0645\u061f",
            "arabic",
            False,
        ),
        (
            "false_positive_guard",
            "\u0645\u0627 \u0647\u0648 IPM\u061f",
            "arabic",
            False,
        ),
    ]
    confusion = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}
    labels_seen: set[str] = set()
    for label, prompt, language, expected in cases:
        labels_seen.add(label)
        predicted = AssistantEngine._heuristic_analysis(
            prompt, language=language, clarification_style="auto", clarification_count=0
        ).needs_clarification
        if expected:
            bucket = "tp" if predicted else "fn"
        else:
            bucket = "fp" if predicted else "tn"
        confusion[bucket] += 1
    assert labels_seen == {"tp", "tn", "false_positive_guard", "false_negative_guard"}
    assert confusion == {"tp": 8, "fp": 0, "tn": 8, "fn": 0}


class _Response:
    status_code = 404
    headers: ClassVar[dict[str, str]] = {}

    def iter_content(self, chunk_size: int):
        del chunk_size
        return iter(())


class _Session:
    def __init__(self) -> None:
        self.urls: list[str] = []

    def get(self, url: str, **kwargs: Any) -> _Response:
        del kwargs
        self.urls.append(url)
        return _Response()


def test_authorized_registry_and_query_relevance_routing() -> None:
    definitions = load_live_source_registry()
    assert len(definitions) >= 9
    assert all(item.authorized and url_is_trusted(item.url) for item in definitions)
    session = _Session()
    client = TrustedSourceClient(
        None, enabled=True, definitions=definitions, session=session
    )  # type: ignore[arg-type]
    result = client.search("registered pesticide Lebanon", category="science")
    assert result.search_requests == 5
    assert session.urls[0].endswith("%D8%A7%D9%84%D9%85%D8%B3%D9%85%D9%88%D8%AD%D8%A9")
    assert not result.verified
