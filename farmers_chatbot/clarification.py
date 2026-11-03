"""Validated, resumable clarification workflow built on official LangGraph primitives."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, Literal, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)

CLARIFICATION_SCHEMA_VERSION = "raise-clarification-v2"
DEFAULT_MAX_CLARIFICATION_ROUNDS = 3
_ARABIC = re.compile(r"[\u0600-\u06ff]")
_LATIN = re.compile(r"[A-Za-z]")


def _meaningful(value: str, *, minimum: int = 2) -> bool:
    return sum(character.isalnum() for character in value) >= minimum


def _clean_unique(values: list[str], *, limit: int) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for raw in values:
        value = " ".join(str(raw).split()).strip()
        key = value.casefold()
        if value and key not in seen:
            cleaned.append(value)
            seen.add(key)
        if len(cleaned) >= limit:
            break
    return cleaned


def _is_other_label(value: str) -> bool:
    normalized = " ".join(value.casefold().split()).strip(" .!?\u060c\u061f")
    return bool(
        re.fullmatch(
            r"(something else|other|another option|"
            r"\u0634\u064a\u0621 \u0622\u062e\u0631|\u062e\u064a\u0627\u0631 \u0622\u062e\u0631|\u063a\u064a\u0631 \u0630\u0644\u0643)",
            normalized,
        )
    )


class ClarificationQuestion(BaseModel):
    """One material clarification field rendered as a typed UI control."""

    model_config = ConfigDict(extra="forbid")

    # Every field is mandatory so the emitted JSON Schema lists all properties in
    # `required`, which strict json_schema mode demands.
    id: str = Field(pattern=r"^[a-z][a-z0-9_]{1,39}$")
    prompt: str = Field(min_length=4, max_length=280)
    answer_type: Literal["single", "multiple", "text"]
    required: bool
    options: list[str] = Field(max_length=6)
    allow_other: bool

    @field_validator("options")
    @classmethod
    def validate_options(cls, values: list[str]) -> list[str]:
        cleaned = _clean_unique(values, limit=6)
        if any(not _meaningful(value) for value in cleaned):
            raise ValueError("clarification question contains punctuation-only options")
        return cleaned

    @model_validator(mode="after")
    def validate_control(self) -> ClarificationQuestion:
        if self.answer_type in {"single", "multiple"} and len(self.options) < 2:
            raise ValueError("choice questions require at least two options")
        if self.answer_type == "text" and self.options:
            raise ValueError("text questions cannot define options")
        if any(_is_other_label(option) for option in self.options):
            self.options = [
                option for option in self.options if not _is_other_label(option)
            ]
            self.allow_other = True
        return self


class StructuredRequestAnalysis(BaseModel):
    """Instructor response contract with semantic, not merely structural, checks."""

    model_config = ConfigDict(extra="forbid")

    intent: str = Field(min_length=3, max_length=160)
    decision: str = Field(min_length=3, max_length=400)
    domain: str = Field(min_length=2, max_length=100)
    risk: Literal["low", "medium", "high"]
    currentness: Literal["stable", "current"]
    location: str | None = Field(max_length=160)
    missing_fields: list[str] = Field(max_length=8)
    needs_clarification: bool
    clarification_question: str | None = Field(max_length=280)
    clarification_options: list[str] = Field(max_length=5)
    clarification_questions: list[ClarificationQuestion] = Field(max_length=3)
    retrieval_queries: list[str] = Field(min_length=1, max_length=4)
    evidence_requirements: list[str] = Field(max_length=8)
    output_shape: str = Field(min_length=2, max_length=160)
    assumptions: list[str] = Field(max_length=8)

    @field_validator(
        "missing_fields",
        "clarification_options",
        "retrieval_queries",
        "evidence_requirements",
        "assumptions",
    )
    @classmethod
    def validate_text_lists(cls, values: list[str], info: ValidationInfo) -> list[str]:
        limit = 5 if info.field_name == "clarification_options" else 8
        cleaned = _clean_unique(values, limit=limit)
        if any(not _meaningful(value) for value in cleaned):
            raise ValueError(f"{info.field_name} contains punctuation-only content")
        return cleaned

    @model_validator(mode="after")
    def validate_clarification(self, info: ValidationInfo) -> StructuredRequestAnalysis:
        if not self.needs_clarification:
            self.clarification_question = None
            self.clarification_options = []
            self.clarification_questions = []
            return self
        questions = list(self.clarification_questions)
        if not questions and self.clarification_question:
            questions = [
                ClarificationQuestion(
                    id="detail",
                    prompt=self.clarification_question,
                    answer_type="single",
                    required=True,
                    options=self.clarification_options,
                    allow_other=any(
                        _is_other_label(option) for option in self.clarification_options
                    ),
                )
            ]
        if not questions:
            raise ValueError("clarification_questions must contain 1-3 questions")
        language = str((info.context or {}).get("language") or "")
        script = _ARABIC if language == "arabic" else _LATIN
        for question in questions:
            if not script.search(question.prompt):
                raise ValueError(
                    "clarification questions must use the user's writing system"
                )
            if any(not script.search(option) for option in question.options):
                raise ValueError(
                    "clarification options must use the user's writing system"
                )
        ids = [question.id for question in questions]
        if len(ids) != len(set(ids)):
            raise ValueError("clarification question IDs must be unique")
        self.clarification_questions = questions[:3]
        primary = self.clarification_questions[0]
        self.clarification_question = primary.prompt
        self.clarification_options = list(primary.options)
        if primary.allow_other:
            self.clarification_options.append(
                "\u0634\u064a\u0621 \u0622\u062e\u0631"
                if language == "arabic"
                else "Something else"
            )
        return self


class ClarificationState(TypedDict, total=False):
    actor_id: str
    conversation_id: str
    original_text: str
    language: str
    mode: str
    clarification_style: str
    history: list[dict[str, str]]
    answers: list[dict[str, str]]
    round: int
    max_rounds: int
    effective_text: str
    analysis: dict[str, Any]
    pending: bool


Planner = Callable[[ClarificationState], Awaitable[StructuredRequestAnalysis]]


@dataclass(frozen=True)
class ClarificationOutcome:
    pending: bool
    analysis: dict[str, Any]
    effective_text: str
    interaction: dict[str, Any]


class ClarificationWorkflow:
    """Small LangGraph sub-workflow; the existing assistant remains canonical."""

    def __init__(self, database_url: str, planner: Planner) -> None:
        self.database_url = database_url.strip()
        self.planner = planner
        self._memory = InMemorySaver()
        self._memory_graph = self._build(self._memory)

    @staticmethod
    def thread_id(actor_id: str, conversation_id: str) -> str:
        digest = hashlib.sha256(f"{actor_id}:{conversation_id}".encode()).hexdigest()
        return f"raise-clarification:{digest}"

    @staticmethod
    def compose_effective_text(state: ClarificationState) -> str:
        original = str(state.get("original_text") or "").strip()
        answers = state.get("answers") or []
        if not answers:
            return original
        details = "\n".join(
            f"- {item['question']}: {item['answer']}" for item in answers
        )
        return f"{original}\n\nClarified user context:\n{details}"

    def _build(self, checkpointer: Any) -> Any:
        workflow = StateGraph(ClarificationState)

        async def analyze(state: ClarificationState) -> dict[str, Any]:
            effective_text = self.compose_effective_text(state)
            plan = await self.planner({**state, "effective_text": effective_text})
            analysis = plan.model_dump(mode="json")
            round_number = int(state.get("round") or 0)
            max_rounds = int(
                state.get("max_rounds") or DEFAULT_MAX_CLARIFICATION_ROUNDS
            )
            pending = bool(plan.needs_clarification and round_number < max_rounds)
            if plan.needs_clarification and not pending:
                analysis["needs_clarification"] = False
                analysis["clarification_question"] = None
                analysis["clarification_options"] = []
                assumptions = list(analysis.get("assumptions") or [])
                assumptions.append(
                    "تابعتُ بعد بلوغ الحد الأقصى من أسئلة الاستيضاح."
                    if state.get("language") == "arabic"
                    else "Proceeded after reaching the clarification-round limit."
                )
                analysis["assumptions"] = _clean_unique(assumptions, limit=8)
            return {
                "analysis": analysis,
                "effective_text": effective_text,
                "pending": pending,
            }

        def ask(state: ClarificationState) -> dict[str, Any]:
            analysis = dict(state["analysis"])
            round_number = int(state.get("round") or 0) + 1
            questions = list(analysis.get("clarification_questions") or [])
            if not questions:
                questions = [
                    {
                        "id": "detail",
                        "prompt": analysis["clarification_question"],
                        "answer_type": "single",
                        "required": True,
                        "options": list(analysis.get("clarification_options") or []),
                        "allow_other": False,
                    }
                ]
            interaction_id = hashlib.sha256(
                (
                    str(state.get("conversation_id"))
                    + ":"
                    + str(round_number)
                    + ":"
                    + "|".join(str(item.get("id")) for item in questions)
                ).encode()
            ).hexdigest()[:24]
            interaction_questions = [
                {
                    "id": str(question["id"]),
                    "prompt": str(question["prompt"]),
                    "answer_type": str(question.get("answer_type") or "single"),
                    "required": bool(question.get("required", True)),
                    "allow_other": bool(question.get("allow_other", False)),
                    "options": [
                        {
                            "id": f"{question['id']}_{index + 1}",
                            "label": label,
                            "value": label,
                            "kind": "standard",
                        }
                        for index, label in enumerate(question.get("options") or [])
                    ],
                }
                for question in questions[:3]
            ]
            interaction = {
                "schema_version": CLARIFICATION_SCHEMA_VERSION,
                "interaction_id": interaction_id,
                "type": "clarification",
                "status": "pending",
                "round": round_number,
                "max_rounds": int(
                    state.get("max_rounds") or DEFAULT_MAX_CLARIFICATION_ROUNDS
                ),
                "questions": interaction_questions,
                "question": interaction_questions[0]["prompt"],
                "options": interaction_questions[0]["options"],
                "missing_fields": list(analysis.get("missing_fields") or []),
                "language": state.get("language"),
            }
            response = interrupt(interaction)
            submitted = response.get("answers") if isinstance(response, dict) else None
            if not isinstance(submitted, dict):
                legacy_value = (
                    response.get("value") or response.get("label") or ""
                    if isinstance(response, dict)
                    else response
                )
                submitted = {interaction_questions[0]["id"]: legacy_value}
            answer = str(
                submitted.get(interaction_questions[0]["id"]) or ""
            ).strip()
            if not _meaningful(answer):
                answer = (
                    "لا أعرف" if state.get("language") == "arabic" else "I don't know"
                )
            submitted.setdefault(interaction_questions[0]["id"], answer)
            answers = list(state.get("answers") or [])
            for question in interaction_questions:
                raw_answer = submitted.get(question["id"])
                if isinstance(raw_answer, list):
                    value = ", ".join(str(item).strip() for item in raw_answer)
                else:
                    value = str(raw_answer or "").strip()
                if not _meaningful(value):
                    value = (
                        "\u0644\u0627 \u0623\u0639\u0631\u0641"
                        if state.get("language") == "arabic"
                        else "I don't know"
                    )
                answers.append(
                    {"question": question["prompt"], "answer": value[:500]}
                )
            return {"answers": answers, "round": round_number, "pending": False}

        workflow.add_node("analyze", analyze)
        workflow.add_node("ask", ask)
        workflow.add_edge(START, "analyze")
        workflow.add_conditional_edges(
            "analyze", lambda state: "ask" if state.get("pending") else END
        )
        workflow.add_edge("ask", "analyze")
        return workflow.compile(checkpointer=checkpointer)

    @asynccontextmanager
    async def _graph(self) -> Any:
        if self.database_url.startswith(("postgres://", "postgresql://")):
            async with AsyncPostgresSaver.from_conn_string(
                self.database_url
            ) as checkpointer:
                yield self._build(checkpointer)
            return
        yield self._memory_graph

    async def advance(
        self,
        *,
        actor_id: str,
        conversation_id: str,
        text: str,
        language: str,
        mode: str,
        clarification_style: str,
        history: list[dict[str, str]],
        clarification_response: dict[str, Any] | None = None,
    ) -> ClarificationOutcome:
        config = {
            "configurable": {"thread_id": self.thread_id(actor_id, conversation_id)}
        }
        async with self._graph() as graph:
            snapshot = await graph.aget_state(config)
            if snapshot.next:
                resume = clarification_response or {"value": text}
                result = await graph.ainvoke(Command(resume=resume), config)
            else:
                result = await graph.ainvoke(
                    {
                        "actor_id": actor_id,
                        "conversation_id": conversation_id,
                        "original_text": text,
                        "language": language,
                        "mode": mode,
                        "clarification_style": clarification_style,
                        "history": history[-6:],
                        "answers": [],
                        "round": 0,
                        "max_rounds": DEFAULT_MAX_CLARIFICATION_ROUNDS,
                        "effective_text": text,
                        "analysis": {},
                        "pending": False,
                    },
                    config,
                )
        interrupts = list(result.get("__interrupt__") or [])
        if interrupts:
            interaction = dict(interrupts[0].value)
            analysis = dict(result.get("analysis") or {})
            return ClarificationOutcome(
                pending=True,
                analysis=analysis,
                effective_text=str(result.get("effective_text") or text),
                interaction=interaction,
            )
        return ClarificationOutcome(
            pending=False,
            analysis=dict(result.get("analysis") or {}),
            effective_text=str(result.get("effective_text") or text),
            interaction={},
        )

    async def delete(self, actor_id: str, conversation_id: str) -> None:
        thread_id = self.thread_id(actor_id, conversation_id)
        if self.database_url.startswith(("postgres://", "postgresql://")):
            async with AsyncPostgresSaver.from_conn_string(
                self.database_url
            ) as checkpointer:
                await checkpointer.adelete_thread(thread_id)
            return
        await self._memory.adelete_thread(thread_id)
