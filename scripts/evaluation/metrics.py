"""Pure deterministic metrics used by the RAISE evaluation harness."""

from __future__ import annotations

import math
import random
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass


def rounded(value: float | None) -> float | None:
    return None if value is None else round(value, 6)


def mean(values: Iterable[float]) -> float | None:
    items = list(values)
    return None if not items else sum(items) / len(items)


def percentile(values: Iterable[float], fraction: float) -> float | None:
    items = sorted(values)
    if not items:
        return None
    if fraction < 0 or fraction > 1:
        raise ValueError("fraction must be between zero and one")
    index = max(0, math.ceil(fraction * len(items)) - 1)
    return items[index]


@dataclass(frozen=True)
class RetrievalScore:
    recall: float | None
    reciprocal_rank: float
    ndcg: float | None


def retrieval_score(
    retrieved_ids: Iterable[str],
    relevance_by_id: dict[str, int],
    top_k: int,
) -> RetrievalScore:
    if top_k < 1:
        raise ValueError("top_k must be positive")
    retrieved = list(retrieved_ids)[:top_k]
    relevant = set(relevance_by_id)
    recall = None if not relevant else len(set(retrieved) & relevant) / len(relevant)
    first_rank = next(
        (rank for rank, item_id in enumerate(retrieved, 1) if item_id in relevant),
        None,
    )
    reciprocal_rank = 0.0 if first_rank is None else 1 / first_rank

    def gain(relevance: int, rank: int) -> float:
        return (2**relevance - 1) / math.log2(rank + 1)

    dcg = sum(
        gain(relevance_by_id.get(item_id, 0), rank)
        for rank, item_id in enumerate(retrieved, 1)
    )
    ideal = sorted(relevance_by_id.values(), reverse=True)[:top_k]
    ideal_dcg = sum(gain(relevance, rank) for rank, relevance in enumerate(ideal, 1))
    ndcg = None if not ideal_dcg else dcg / ideal_dcg
    return RetrievalScore(recall=recall, reciprocal_rank=reciprocal_rank, ndcg=ndcg)


def graph_path_accuracy(
    predicted: Iterable[tuple[str, ...]],
    expected: Iterable[tuple[str, ...]],
) -> float | None:
    predicted_set = set(predicted)
    expected_set = set(expected)
    if not expected_set:
        return None
    union = predicted_set | expected_set
    return len(predicted_set & expected_set) / len(union)


@dataclass(frozen=True)
class NormalizedPreference:
    case_id: str
    system_a: str
    system_b: str
    score_a: float
    tied: bool


def normalize_preference(
    case_id: str,
    system_a: str,
    system_b: str,
    winner: str,
) -> NormalizedPreference:
    first, second = sorted((system_a, system_b))
    if winner == "tie":
        score = 0.5
    else:
        winner_system = system_a if winner == "a" else system_b
        score = 1.0 if winner_system == first else 0.0
    return NormalizedPreference(
        case_id=case_id,
        system_a=first,
        system_b=second,
        score_a=score,
        tied=winner == "tie",
    )


def pairwise_bootstrap(
    judgments: Iterable[NormalizedPreference],
    *,
    seed: int = 1729,
    resamples: int = 2000,
    confidence: float = 0.95,
) -> list[dict[str, object]]:
    if resamples < 1:
        raise ValueError("resamples must be positive")
    if confidence <= 0 or confidence >= 1:
        raise ValueError("confidence must be between zero and one")
    grouped: dict[tuple[str, str], list[NormalizedPreference]] = defaultdict(list)
    for judgment in judgments:
        grouped[(judgment.system_a, judgment.system_b)].append(judgment)
    output: list[dict[str, object]] = []
    for pair in sorted(grouped):
        values = grouped[pair]
        by_case: dict[str, list[float]] = defaultdict(list)
        for value in values:
            by_case[value.case_id].append(value.score_a)
        case_scores = [mean(by_case[case_id]) for case_id in sorted(by_case)]
        scores = [value for value in case_scores if value is not None]
        observed = mean(scores)
        rng = random.Random(f"{seed}:{pair[0]}:{pair[1]}")
        samples = [
            mean(rng.choice(scores) for _ in range(len(scores)))
            for _ in range(resamples)
        ]
        alpha = (1 - confidence) / 2
        output.append(
            {
                "system_a": pair[0],
                "system_b": pair[1],
                "score_a": rounded(observed),
                "score_b": rounded(None if observed is None else 1 - observed),
                "confidence": confidence,
                "ci_lower_a": rounded(percentile(samples, alpha)),
                "ci_upper_a": rounded(percentile(samples, 1 - alpha)),
                "case_count": len(scores),
                "judgment_count": len(values),
                "tie_fraction": rounded(
                    sum(value.tied for value in values) / len(values)
                ),
                "bootstrap_seed": seed,
                "bootstrap_resamples": resamples,
                "bootstrap_unit": "case",
            }
        )
    return output
