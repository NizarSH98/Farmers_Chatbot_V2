
import pytest

from farmers_chatbot.llm import AssistantService
from farmers_chatbot.tools import ToolRegistry


class FakeResponse:
    status_code = 200

    def __init__(self, content="Grounded answer [AKKAR-PROFILE-001]"):
        self.content = content

    def json(self):
        return {"choices": [{"message": {"content": self.content}}]}


def test_missing_key_returns_retrieval_fallback(knowledge, store):
    service = AssistantService(knowledge, ToolRegistry(knowledge, store), api_key="")
    response = service.answer("What is important about potatoes in Akkar?")
    assert response.sources
    assert response.model is None
    assert response.warning


def test_current_question_is_not_duplicated_in_history(monkeypatch, knowledge, store):
    captured = {}

    def fake_post(url, headers, json, timeout):
        captured.update(json)
        return FakeResponse()

    monkeypatch.setattr("farmers_chatbot.llm.requests.post", fake_post)
    service = AssistantService(
        knowledge,
        ToolRegistry(knowledge, store),
        api_key="test-placeholder",
    )
    service.answer(
        "current question",
        conversation_history=[
            {"role": "user", "content": "previous question"},
            {"role": "assistant", "content": "previous answer"},
        ],
    )
    raw_messages = captured["messages"]
    assert sum(
        "current question" in str(message.get("content", ""))
        for message in raw_messages
    ) == 1
    assert any(message.get("content") == "previous question" for message in raw_messages)


def test_requested_model_and_privacy_routing_are_applied(
    monkeypatch,
    knowledge,
    store,
):
    captured = {}

    def fake_post(url, headers, json, timeout):
        captured.update(json)
        return FakeResponse()

    monkeypatch.setattr("farmers_chatbot.llm.requests.post", fake_post)
    service = AssistantService(
        knowledge,
        ToolRegistry(knowledge, store),
        api_key="test-placeholder",
    )
    response = service.answer(
        "Summarize this farm question",
        model_id="minimax/minimax-m3",
    )
    assert response.model == "minimax/minimax-m3"
    assert captured["model"] == "minimax/minimax-m3"
    assert captured["provider"] == {
        "data_collection": "deny",
        "zdr": True,
    }


def test_unapproved_requested_model_is_rejected(knowledge, store):
    service = AssistantService(
        knowledge,
        ToolRegistry(knowledge, store),
        api_key="test-placeholder",
    )
    with pytest.raises(ValueError, match="not enabled"):
        service.answer("Test", model_id="unapproved/example-model")


def test_tool_follow_up_preserves_provider_message_metadata(
    monkeypatch,
    knowledge,
    store,
):
    payloads = []

    def fake_post(url, headers, json, timeout):
        payloads.append(json)
        if len(payloads) == 1:
            response = FakeResponse()
            response.json = lambda: {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "reasoning_details": [{"type": "encrypted", "data": "opaque"}],
                            "tool_calls": [
                                {
                                    "id": "call-1",
                                    "type": "function",
                                    "function": {
                                        "name": "convert_agricultural_units",
                                        "arguments": (
                                            '{"value": 1, "from_unit": "hectare", '
                                            '"to_unit": "dunam"}'
                                        ),
                                    },
                                }
                            ],
                        }
                    }
                ]
            }
            return response
        return FakeResponse("One hectare is 10 dunams.")

    monkeypatch.setattr("farmers_chatbot.llm.requests.post", fake_post)
    service = AssistantService(
        knowledge,
        ToolRegistry(knowledge, store),
        api_key="test-placeholder",
    )
    response = service.answer(
        "Convert one hectare to dunams",
        model_id="moonshotai/kimi-k3",
    )
    assert response.success
    continued_message = payloads[1]["messages"][-2]
    assert continued_message["reasoning_details"][0]["data"] == "opaque"


def test_source_only_prompt_disables_general_knowledge(monkeypatch, knowledge, store):
    captured = {}

    def fake_post(url, headers, json, timeout):
        captured.update(json)
        return FakeResponse()

    monkeypatch.setattr("farmers_chatbot.llm.requests.post", fake_post)
    service = AssistantService(
        knowledge,
        ToolRegistry(knowledge, store),
        api_key="test-placeholder",
    )
    service.answer("Tell me about Akkar", mode_key="source_only")
    assert "Use only the supplied project knowledge" in captured["messages"][0]["content"]

