from __future__ import annotations

from farmers_chatbot.qdrant_retrieval import QdrantGraphRetrieval
from farmers_chatbot.retrieval import RetrievalRequest


def _request(**changes: object) -> RetrievalRequest:
    values: dict[str, object] = {
        "query": "potato irrigation",
        "language": "en",
        "mode": "quick",
    }
    values.update(changes)
    return RetrievalRequest(**values)  # type: ignore[arg-type]


def test_adaptive_route_is_bounded_and_deterministic() -> None:
    assert QdrantGraphRetrieval.route(_request()) == "vector"
    assert QdrantGraphRetrieval.route(_request(mode="standard")) == "contextual"
    assert QdrantGraphRetrieval.route(_request(mode="deep")) == "lazy_graph"
    assert (
        QdrantGraphRetrieval.route(_request(query="compare soil and irrigation"))
        == "lazy_graph"
    )


def test_route_override_rejects_unknown_values() -> None:
    request = _request(route_override="unbounded")
    try:
        QdrantGraphRetrieval.route(request)
    except ValueError as exc:
        assert "unsupported retrieval route" in str(exc)
    else:
        raise AssertionError("unknown retrieval route was accepted")


def test_personalized_pagerank_only_uses_retrieved_subgraph() -> None:
    paths = [
        {"id": "r1", "subject_entity_id": "a", "object_entity_id": "b", "depth": 1},
        {"id": "r2", "subject_entity_id": "b", "object_entity_id": "c", "depth": 2},
        {"id": "r3", "subject_entity_id": "x", "object_entity_id": "y", "depth": 1},
    ]
    ranked = QdrantGraphRetrieval._personalized_pagerank(paths, ("a",))
    assert {item["id"] for item in ranked} == {"r1", "r2", "r3"}
    assert all("personalized_pagerank" in item for item in ranked)
