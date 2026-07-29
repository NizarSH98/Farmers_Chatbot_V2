from dataclasses import dataclass

from farmers_chatbot.tools import ToolRegistry


@dataclass
class _Result:
    def to_dict(self):
        return {
            "available": True,
            "verified": True,
            "citations": [],
            "search_requests": 1,
        }


class _Client:
    def __init__(self):
        self.calls = 0

    def search(self, query, category):
        del query, category
        self.calls += 1
        return _Result()


def test_trusted_search_is_capped_at_two_calls_per_answer(knowledge, store):
    client = _Client()
    registry = ToolRegistry(knowledge, store, trusted_client=client)
    registry.search_trusted_sources("one")
    registry.search_trusted_sources("two")
    capped = registry.search_trusted_sources("three")
    assert client.calls == 2
    assert not capped["available"]
    assert "limit" in capped["warning"].lower()
