from __future__ import annotations

import math

import pytest

from scripts.evaluation.metrics import (
    graph_path_accuracy,
    normalize_preference,
    pairwise_bootstrap,
    retrieval_score,
)


def test_retrieval_metrics_use_rank_and_graded_relevance() -> None:
    score = retrieval_score(
        ["irrelevant", "high", "low"],
        {"high": 3, "low": 1},
        top_k=3,
    )
    expected_dcg = 7 / math.log2(3) + 1 / math.log2(4)
    ideal_dcg = 7 / math.log2(2) + 1 / math.log2(3)

    assert score.recall == 1
    assert score.reciprocal_rank == 0.5
    assert score.ndcg == pytest.approx(expected_dcg / ideal_dcg)


def test_graph_paths_use_exact_sequence_jaccard() -> None:
    expected = [("a", "rel", "b"), ("b", "rel", "c")]
    predicted = [("a", "rel", "b"), ("c", "rel", "b")]

    assert graph_path_accuracy(predicted, expected) == pytest.approx(1 / 3)
    assert graph_path_accuracy([], []) is None


def test_pairwise_bootstrap_is_orientation_safe_and_reproducible() -> None:
    judgments = [
        normalize_preference("c1", "system-z", "system-a", "a"),
        normalize_preference("c1", "system-a", "system-z", "b"),
        normalize_preference("c2", "system-a", "system-z", "tie"),
    ]

    first = pairwise_bootstrap(judgments, seed=10, resamples=250)
    second = pairwise_bootstrap(judgments, seed=10, resamples=250)

    assert first == second
    assert first[0]["system_a"] == "system-a"
    assert first[0]["score_a"] == pytest.approx(0.25)
    assert first[0]["bootstrap_unit"] == "case"
