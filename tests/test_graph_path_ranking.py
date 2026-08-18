from __future__ import annotations

from farmers_chatbot.qdrant_retrieval import QdrantGraphRetrieval


def test_direct_endpoints_and_named_predicate_rank_first() -> None:
    paths = [
        {
            "id": "popular",
            "subject_entity_id": "seed-a",
            "object_entity_id": "other",
            "predicate": "related_to",
            "depth": 1,
            "personalized_pagerank": 0.9,
        },
        {
            "id": "exact",
            "subject_entity_id": "seed-a",
            "object_entity_id": "seed-b",
            "predicate": "supports_action",
            "depth": 1,
            "personalized_pagerank": 0.1,
        },
    ]

    ranked = QdrantGraphRetrieval._rank_graph_paths(
        paths,
        ("seed-a", "seed-b"),
        "Explain how A supports action B",
    )

    assert ranked[0]["id"] == "exact"
    assert ranked[0]["query_path_score"] > ranked[1]["query_path_score"]
