import json

import pytest

from farmers_chatbot.tools import ToolRegistry


def test_search_tool_returns_structured_local_results(knowledge, store):
    tools = ToolRegistry(knowledge, store)
    result = json.loads(
        tools.execute(
            "search_knowledge",
            {"query": "ESDU livestock work in Akkar", "language": "english", "top_k": 3},
        )
    )
    assert result["results"]
    assert any("ESDU" in item["item_id"] or "LIVESTOCK" in item["item_id"] for item in result["results"])


def test_unknown_tool_is_rejected(knowledge, store):
    tools = ToolRegistry(knowledge, store)
    assert json.loads(tools.execute("run_shell", {}))["error"] == "unknown_tool"


def test_feedback_requires_consent(knowledge, store):
    tools = ToolRegistry(knowledge, store)
    with pytest.raises(ValueError):
        tools.record_feedback(
            session_id="test",
            category="usability",
            comment="Needs larger text",
            consent=False,
        )


def test_feedback_is_recorded_without_external_user_id(knowledge, store):
    tools = ToolRegistry(knowledge, store)
    result = tools.record_feedback(
        session_id="test",
        category="local_language",
        comment="Use a more familiar Akkar term.",
        consent=True,
        rating=4,
        language="english",
    )
    assert result["recorded"] is True
    assert store.feedback_summary()["total_feedback"] == 1

