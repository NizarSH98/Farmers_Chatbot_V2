"""Safety and bounded-tool regressions for the canonical assistant engine."""

from __future__ import annotations

import json
import time

import pytest

from farmers_chatbot.assistant_contracts import TurnCommand
from farmers_chatbot.assistant_pipeline import AssistantEngine
from farmers_chatbot.knowledge import KnowledgeIndex
from farmers_chatbot.provider import ProviderResponse, ProviderUsage
from farmers_chatbot.storage import EvidenceStore
from farmers_chatbot.tool_executor import ToolExecutor
from farmers_chatbot.tools import ToolRegistry


class _Registry:
    def model_definitions(self):
        return [
            {
                "type": "function",
                "function": {
                    "name": "echo",
                    "parameters": {
                        "type": "object",
                        "properties": {"text": {"type": "string"}},
                        "required": ["text"],
                        "additionalProperties": False,
                    },
                },
            }
        ]

    def execute(self, name, arguments):
        if arguments["text"] == "slow":
            time.sleep(0.05)
        return arguments["text"]


@pytest.mark.asyncio
async def test_tool_executor_reports_total_budget_and_timeout() -> None:
    executor = ToolExecutor(  # type: ignore[arg-type]
        _Registry(), timeout_seconds=1.0, max_parallel_calls=2, max_total_calls=1
    )
    calls = [
        {
            "id": f"call-{index}",
            "function": {"name": "echo", "arguments": json.dumps({"text": text})},
        }
        for index, text in enumerate(("ok", "extra", "extra-2"))
    ]
    results = await executor.execute_many(calls)
    assert results[0].success is True
    assert [item.error_type for item in results[1:]] == [
        "budget_exceeded",
        "budget_exceeded",
    ]

    timeout_executor = ToolExecutor(  # type: ignore[arg-type]
        _Registry(), timeout_seconds=0.001, max_total_calls=1
    )
    timeout = await timeout_executor.execute(
        {
            "id": "slow-call",
            "function": {"name": "echo", "arguments": {"text": "slow"}},
        }
    )
    assert timeout.success is False
    assert timeout.error_type == "timeout"


@pytest.mark.asyncio
async def test_offline_high_risk_request_emits_only_safe_refusal(tmp_path) -> None:
    knowledge = KnowledgeIndex.from_directory()
    tools = ToolRegistry(knowledge, EvidenceStore(tmp_path / "evidence.sqlite3"))
    engine = AssistantEngine(knowledge, api_key="")
    command = TurnCommand(
        request_id="offline-risk",
        actor_id="actor",
        channel="test",
        conversation_id="conversation",
        text="Give me the exact pesticide dose for this crop",
        clarification_style="direct",
    )
    prepared = await engine.prepare(
        command, tools=tools, history=[], clarification_count=0
    )
    events = [
        event
        async for event in engine.stream(command, prepared, tools=tools, history=[])
    ]
    result = next(event.result for event in events if event.result is not None)
    streamed = "".join(
        str(event.data.get("text") or "")
        for event in events
        if event.event == "content.delta"
    )
    assert result.kind == "refusal"
    assert "cannot confirm" in result.content
    assert streamed == result.content
    assert "exact pesticide dose" not in streamed
    await engine.close()


class _RejectingProvider:
    api_key = "provider-key"

    def __init__(self) -> None:
        self.records = []

    async def close(self) -> None:
        return None

    async def complete(self, *, stage, payload, timeout=45.0):
        del payload, timeout
        if stage == "analyzer":
            content = json.dumps(
                {
                    "intent": "treatment",
                    "decision": "choose treatment",
                    "domain": "agriculture",
                    "risk": "high",
                    "currentness": "stable",
                    "needs_clarification": False,
                    "retrieval_queries": ["tomato pesticide dose"],
                    "evidence_requirements": ["approved label"],
                    "output_shape": "safe limitation",
                }
            )
        elif stage.startswith("generation_round_"):
            content = "Apply 20 milliliters immediately without checking the label."
        elif stage == "verifier":
            content = json.dumps(
                {"approved": False, "revised_answer": "", "warning": "unsupported"}
            )
        else:  # pragma: no cover - makes unexpected provider stages visible
            raise AssertionError(stage)
        return ProviderResponse(
            message={"role": "assistant", "content": content},
            usage=ProviderUsage(),
            raw={},
        )


@pytest.mark.asyncio
async def test_rejected_high_risk_draft_is_never_streamed(tmp_path) -> None:
    knowledge = KnowledgeIndex.from_directory()
    tools = ToolRegistry(knowledge, EvidenceStore(tmp_path / "evidence.sqlite3"))
    engine = AssistantEngine(knowledge, provider=_RejectingProvider())  # type: ignore[arg-type]
    command = TurnCommand(
        request_id="rejected-risk",
        actor_id="actor",
        channel="test",
        conversation_id="conversation",
        text="What pesticide dose should I use on tomatoes?",
        clarification_style="direct",
    )
    prepared = await engine.prepare(
        command, tools=tools, history=[], clarification_count=0
    )
    events = [
        event
        async for event in engine.stream(command, prepared, tools=tools, history=[])
    ]
    result = next(event.result for event in events if event.result is not None)
    streamed = "".join(
        str(event.data.get("text") or "")
        for event in events
        if event.event == "content.delta"
    )
    assert result.kind == "refusal"
    assert "cannot confirm" in streamed
    assert "20 milliliters" not in streamed
    await engine.close()
