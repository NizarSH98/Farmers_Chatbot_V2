import json

import httpx
import pytest

from farmers_chatbot.assistant_pipeline import AssistantEngine
from farmers_chatbot.config import MODE_PROFILES, resolve_model_id
from farmers_chatbot.llm import (
    AssistantPromptBuilder,
    AssistantRequest,
    AssistantResponse,
    AssistantService,
    extract_follow_up_questions,
)
from farmers_chatbot.provider import ProviderClient, ProviderResponse, ProviderUsage
from farmers_chatbot.tool_executor import ToolExecutor
from farmers_chatbot.tools import ToolRegistry


def _messages(builder, knowledge, *, query="current question", mode="standard"):
    return builder._build_messages(
        query=query,
        sources=knowledge.search(query, language="english", top_k=3),
        project_sources=[],
        trusted_context="",
        language="english",
        profile=MODE_PROFILES[mode],
        history=[
            {"role": "user", "content": "previous question"},
            {"role": "assistant", "content": "previous answer"},
        ],
        clarification_style="auto",
        attachments=[],
        verification_required=False,
        project_instructions="",
    )


def test_missing_key_compatibility_facade_returns_canonical_fallback(knowledge, store):
    service = AssistantService(knowledge, ToolRegistry(knowledge, store), api_key="")
    response = service.answer("What is important about potatoes in Akkar?")
    assert response.sources == []
    assert response.model is None
    assert response.answer


def test_assistant_service_is_only_a_unified_facade(monkeypatch, knowledge, store):
    captured = {}

    def fake_answer(self, request, *, conversation_history=None):
        del self
        captured["request"] = request
        captured["history"] = conversation_history
        return AssistantResponse(
            answer="canonical",
            sources=[],
            model=None,
            mode=request.mode,
            language="english",
            duration_ms=1,
        )

    monkeypatch.setattr(
        "farmers_chatbot.assistant_compat.UnifiedAssistantFacade.answer_request",
        fake_answer,
    )
    service = AssistantService(knowledge, ToolRegistry(knowledge, store), api_key="")
    response = service.answer(
        "one request",
        conversation_history=[{"role": "user", "content": "prior"}],
    )
    assert response.answer == "canonical"
    assert captured["request"].text == "one request"
    assert captured["history"][0]["content"] == "prior"


def test_prompt_builder_does_not_duplicate_current_question(knowledge, store):
    builder = AssistantPromptBuilder(knowledge, ToolRegistry(knowledge, store))
    messages = _messages(builder, knowledge)
    assert sum(
        "current question" in str(message.get("content", ""))
        for message in messages
    ) == 1
    assert any(message.get("content") == "previous question" for message in messages)


def test_source_only_prompt_disables_general_knowledge(knowledge, store):
    builder = AssistantPromptBuilder(knowledge, ToolRegistry(knowledge, store))
    messages = _messages(builder, knowledge, query="Tell me about Akkar", mode="source_only")
    assert "Use only the supplied project knowledge" in messages[0]["content"]


@pytest.mark.asyncio
async def test_provider_client_is_only_http_boundary_and_applies_privacy_policy():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(json.loads(request.content))
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "answer"}}], "usage": {}},
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = ProviderClient(api_key="test-key", client=client)
    result = await provider.complete(
        stage="generation_round_1",
        payload={"model": "minimax/minimax-m3", "messages": []},
    )
    assert result.message["content"] == "answer"
    assert captured["provider"] == {"data_collection": "deny", "zdr": True}
    assert provider.records[0].stage == "generation_round_1"
    await client.aclose()


def test_unapproved_requested_model_is_rejected():
    with pytest.raises(ValueError, match="not enabled"):
        resolve_model_id("unapproved/example-model", MODE_PROFILES["standard"].model)


class _ToolLoopProvider:
    api_key = "provider-key"

    def __init__(self):
        self.records = []
        self.payloads = []

    async def close(self):
        return None

    async def complete(self, *, stage, payload, timeout=45.0):
        del stage, timeout
        self.payloads.append(payload)
        if len(self.payloads) == 1:
            message = {
                "role": "assistant",
                "content": None,
                "reasoning_details": [{"type": "encrypted", "data": "opaque"}],
                "tool_calls": [
                    {
                        "id": "call-1",
                        "type": "function",
                        "function": {
                            "name": "convert_agricultural_units",
                            "arguments": json.dumps(
                                {
                                    "value": 1,
                                    "from_unit": "hectare",
                                    "to_unit": "dunam",
                                }
                            ),
                        },
                    },
                    {
                        "id": "call-2",
                        "type": "function",
                        "function": {
                            "name": "get_logframe_status",
                            "arguments": "{}",
                        },
                    },
                ],
            }
        else:
            message = {"role": "assistant", "content": "Both tools ran."}
        return ProviderResponse(message=message, usage=ProviderUsage(), raw={})


@pytest.mark.asyncio
async def test_canonical_tool_loop_preserves_metadata_and_executes_parallel_calls(
    knowledge,
    store,
):
    registry = ToolRegistry(knowledge, store)
    provider = _ToolLoopProvider()
    engine = AssistantEngine(knowledge, provider=provider)  # type: ignore[arg-type]
    answer, _, _, tools = await engine._generate_with_tools(
        messages=[{"role": "user", "content": "run both"}],
        profile=MODE_PROFILES["standard"],
        executor=ToolExecutor(registry, max_total_calls=4),
    )
    assert answer == "Both tools ran."
    assert set(tools) == {"convert_agricultural_units", "get_logframe_status"}
    assert provider.payloads[0]["parallel_tool_calls"] is True
    continued = provider.payloads[1]["messages"][-3]
    assert continued["reasoning_details"][0]["data"] == "opaque"


def test_extract_follow_up_questions_splits_trailing_marker_line():
    content = (
        "Plant potatoes in March.\n\n"
        "FOLLOWUP: When should I irrigate? | What variety suits Akkar? | Is frost a risk?"
    )
    cleaned, questions = extract_follow_up_questions(content)
    assert cleaned == "Plant potatoes in March."
    assert questions == [
        "When should I irrigate?",
        "What variety suits Akkar?",
        "Is frost a risk?",
    ]


def test_extract_follow_up_questions_no_marker_is_a_no_op():
    content = "Plant potatoes in March."
    cleaned, questions = extract_follow_up_questions(content)
    assert cleaned == content
    assert questions == []


def test_extract_follow_up_questions_caps_at_three():
    _, questions = extract_follow_up_questions(
        "Answer.\nFOLLOWUP: a? | b? | c? | d?"
    )
    assert questions == ["a?", "b?", "c?"]


def test_request_type_remains_compatible():
    request = AssistantRequest(
        user_id="user",
        channel="web",
        conversation_id="conversation",
        project_id=None,
        text="question",
    )
    assert request.mode == "standard"
