import json

import httpx
import pytest

from farmers_chatbot.assistant_pipeline import AsyncAssistantPipeline
from farmers_chatbot.llm import AssistantRequest

pytestmark = pytest.mark.asyncio(loop_scope="function")


ANALYSIS_RESPONSE = {
    "intent": "irrigation_planning",
    "decision": "When to irrigate potatoes",
    "domain": "irrigation",
    "risk": "low",
    "currentness": "stable",
    "location": "Akkar",
    "missing_fields": [],
    "needs_clarification": False,
    "clarification_question": None,
    "clarification_options": [],
    "clarification_questions": [],
    "retrieval_queries": ["potato irrigation Akkar"],
    "evidence_requirements": [],
    "output_shape": "short_answer",
    "assumptions": [],
}


async def test_analyzer_requests_strict_json_schema(knowledge):
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["payload"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"message": {"content": json.dumps(ANALYSIS_RESPONSE)}}
                ]
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    pipeline = AsyncAssistantPipeline(knowledge, api_key="test-key", client=client)
    try:
        analysis = await pipeline._analyze(
            AssistantRequest(
                user_id="user",
                channel="web",
                conversation_id="conversation",
                project_id=None,
                text="When should I irrigate my potatoes?",
            ),
            language="english",
            history=[],
            clarification_count=0,
        )
    finally:
        await client.aclose()

    response_format = captured["payload"]["response_format"]
    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["strict"] is True
    schema = response_format["json_schema"]["schema"]
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == set(schema["properties"])
    assert schema["properties"]["risk"]["enum"] == ["low", "medium", "high"]

    assert analysis.intent == "irrigation_planning"
    assert analysis.retrieval_queries == ("potato irrigation Akkar",)
    assert analysis.needs_clarification is False


async def test_analyzer_is_told_about_attached_photos(knowledge):
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["payload"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": json.dumps(ANALYSIS_RESPONSE)}}]},
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    pipeline = AsyncAssistantPipeline(knowledge, api_key="test-key", client=client)
    try:
        await pipeline._analyze(
            AssistantRequest(
                user_id="user",
                channel="web",
                conversation_id="conversation",
                project_id=None,
                text="Please analyze this image.",
                attachments=[{"kind": "image", "data_url": "data:image/png;base64,AAAA"}],
            ),
            language="english",
            history=[],
            clarification_count=0,
        )
    finally:
        await client.aclose()

    messages = captured["payload"]["messages"]
    text_part, image_part = messages[-1]["content"]
    assert json.loads(text_part["text"])["attached_images"] == 1
    assert image_part == {
        "type": "image_url",
        "image_url": {"url": "data:image/png;base64,AAAA"},
    }
    assert "never ask the user to" in messages[0]["content"]
