"""Graph-found passages join evidence fusion as a bounded, review-gated channel."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from farmers_chatbot import qdrant_retrieval
from farmers_chatbot.qdrant_retrieval import QdrantGraphRetrieval
from farmers_chatbot.retrieval import RetrievalRequest


def _point(point_id: str, record_id: str | None = None):
    return SimpleNamespace(id=point_id, payload={"record_id": record_id or point_id, "record_type": "chunk"})


def test_fuse_channel_adds_weighted_reciprocal_rank_with_offset():
    scores = {"a": 0.5}
    points = {"a": _point("a")}
    QdrantGraphRetrieval._fuse_channel(scores, points, [_point("a"), _point("b")], weight=2.0, rank_offset=1)
    assert scores["a"] == pytest.approx(0.5 + 2.0 / 62)
    assert scores["b"] == pytest.approx(2.0 / 63)
    assert set(points) == {"a", "b"}


class _ScrollClient:
    def __init__(self, records):
        self.records = records
        self.calls = []

    async def scroll(self, **kwargs):
        self.calls.append(kwargs)
        wanted = None
        for condition in kwargs["scroll_filter"].must:
            if condition.key == "record_id":
                wanted = set(condition.match.any)
        return [record for record in self.records if record.payload["record_id"] in wanted], None


def _service(client) -> QdrantGraphRetrieval:
    service = object.__new__(QdrantGraphRetrieval)
    service.client = client
    service.deployment_scope = "pilot"
    return service


@pytest.mark.asyncio
async def test_graph_passages_follow_path_order_and_respect_review_status():
    client = _ScrollClient([_point("p3", "chunk_3"), _point("p1", "chunk_1"), _point("p2", "chunk_2")])
    service = _service(client)
    paths = [
        {"passage_ids": ["chunk_2", "chunk_1"]},
        {"passage_ids": ["chunk_1", "chunk_3"]},
    ]
    request = RetrievalRequest(query="q", language="en", mode="deep")

    ranked = await service._graph_passage_points(request, "release", {"evidence_collection": "evidence"}, paths)

    assert [point.payload["record_id"] for point in ranked] == ["chunk_2", "chunk_1", "chunk_3"]
    conditions = {condition.key: condition.match for condition in client.calls[0]["scroll_filter"].must}
    assert conditions["release_id"].value == "release"
    assert conditions["record_type"].value == "chunk"
    assert list(conditions["review_status"].any) == service._statuses(request)


@pytest.mark.asyncio
async def test_graph_passages_are_bounded_and_skip_empty_paths(monkeypatch):
    monkeypatch.setattr(qdrant_retrieval, "GRAPH_PASSAGE_LIMIT", 2)
    client = _ScrollClient([_point(f"p{index}", f"chunk_{index}") for index in range(5)])
    service = _service(client)
    request = RetrievalRequest(query="q", language="en", mode="deep")

    assert await service._graph_passage_points(request, "release", {"evidence_collection": "e"}, []) == []
    assert client.calls == []

    paths = [{"passage_ids": [f"chunk_{index}" for index in range(5)]}]
    ranked = await service._graph_passage_points(request, "release", {"evidence_collection": "e"}, paths)
    assert [point.payload["record_id"] for point in ranked] == ["chunk_0", "chunk_1"]


def test_graph_channel_is_limited_to_the_multi_hop_route():
    assert qdrant_retrieval.GRAPH_CHANNEL_ROUTES == frozenset({"lazy_graph"})
