
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

