from __future__ import annotations

from scripts.benchmark_embeddings import select_candidate


def _candidate(name: str, *, ndcg: float, recall: float = 0.9, gap: float = 0.04,
               latency: float = 250, cost: float = 1.0) -> dict[str, object]:
    return {
        "candidate_id": name,
        "ndcg_at_10": ndcg,
        "recall_at_10": recall,
        "language_gap": gap,
        "retrieval_p95_ms": latency,
        "estimated_cost_usd": cost,
    }


def test_selects_lowest_cost_within_one_point_of_best() -> None:
    selected = select_candidate(
        [
            _candidate("best", ndcg=0.91, cost=2),
            _candidate("economical", ndcg=0.901, cost=1),
            _candidate("too_far", ndcg=0.899, cost=0.1),
        ]
    )
    assert selected and selected["candidate_id"] == "economical"


def test_blocks_vector_cutover_when_any_hard_gate_fails() -> None:
    assert select_candidate(
        [
            _candidate("recall", ndcg=0.9, recall=0.89),
            _candidate("language", ndcg=0.9, gap=0.05),
            _candidate("latency", ndcg=0.9, latency=300),
        ]
    ) is None
