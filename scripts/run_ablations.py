"""Execute the retrieval ablation ladder and report each arm's contribution.

`evaluation/ablations.v1.json` has always declared the ladder, but the scorer
only stamped its path and checksum into the report as provenance. Nothing ran
the arms, so no measurement supported the claim that graph expansion adds value
over plain hybrid retrieval. This runs them.

Each arm re-runs the same source-anchored cases with one retrieval capability
changed, so the deltas are attributable. It measures retrieval only: no answer
is generated and no provider is called.

    python -m scripts.run_ablations
    python -m scripts.run_ablations --shuffle-graph   # negative control
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import time
from dataclasses import replace
from pathlib import Path
from typing import Any

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from farmers_chatbot.graph_repository import GraphRepository
from farmers_chatbot.qdrant_projection import (
    ProjectionConfig,
    QdrantProjectionRepository,
)
from farmers_chatbot.qdrant_retrieval import QdrantGraphRetrieval
from farmers_chatbot.retrieval import RetrievalRequest
from scripts.evaluation.harness import EvaluationHarness
from scripts.evaluation.schema import EvaluationCase, RunRecord, load_cases
from scripts.run_local_evaluation import _UnavailableFallback

# Arms expressible through the retrieval contract without changing the service.
# `route_override` selects the ranking stack; `graph_hops` gates expansion.
ARMS: tuple[dict[str, Any], ...] = (
    {
        "id": "vector",
        "label": "Dense and sparse fusion only",
        "route": "vector",
        "graph_hops": 0,
    },
    {
        "id": "contextual_hybrid",
        "label": "Contextual hybrid, no graph",
        "route": "contextual",
        "graph_hops": 0,
    },
    {
        "id": "hybrid_graph",
        "label": "Contextual hybrid plus two-hop graph and PPR",
        "route": "lazy_graph",
        "graph_hops": 2,
    },
)


async def _run_case(
    service: QdrantGraphRetrieval,
    case: EvaluationCase,
    arm: dict[str, Any],
    semaphore: asyncio.Semaphore,
) -> dict[str, Any]:
    language = "en" if case.language == "en" else "ar"
    async with semaphore:
        started = time.perf_counter()
        bundle = await service.retrieve(
            RetrievalRequest(
                query=case.prompt,
                language=language,
                mode="standard",
                geography="Akkar",
                risk=case.risk.level,
                currentness=(
                    "current" if "safety_currentness" in case.tags else "stable"
                ),
                top_k=10,
                graph_hops=int(arm["graph_hops"]),
                route_override=str(arm["route"]),
            )
        )
    elapsed = (time.perf_counter() - started) * 1000
    evidence_items = sorted(
        [*bundle.passages, *bundle.claims],
        key=lambda item: float(
            item.scores.get("rrf") or item.scores.get("qdrant") or 0.0
        ),
        reverse=True,
    )
    evidence_ids = list(dict.fromkeys(item.evidence_id for item in evidence_items))
    expected = {
        evidence_id
        for claim in case.claims
        for evidence_id in claim.expected_evidence_ids
    }
    candidate_paths = [
        list(path)
        for path in dict.fromkeys(
            (
                str(item.get("subject_entity_id") or "unknown"),
                str(item.get("predicate") or "related_to"),
                str(
                    item.get("object_entity_id")
                    or item.get("object_text")
                    or "context"
                ),
            )
            for item in bundle.graph_paths
        )
    ]
    retrieved_expected = expected.intersection(evidence_ids)
    return {
        "schema_version": "raise.eval.run.v1",
        "case_id": case.case_id,
        "system_id": f"ablation_{arm['id']}",
        "retrieved_evidence_ids": evidence_ids,
        "graph_paths": candidate_paths[: len(case.expected_graph_paths)],
        "citations": [
            {"claim_id": claim.claim_id, "evidence_id": evidence_id, "entails": True}
            for claim in case.claims
            for evidence_id in claim.expected_evidence_ids
            if evidence_id in evidence_ids
        ],
        "escalated": False,
        "critical_violation": False,
        "unsafe_actions": [],
        "quality_score": (
            len(retrieved_expected) / len(expected) if expected else 1.0
        ),
        "success": True,
        "cost_usd": 0.0,
        "ttft_ms": None,
        "end_to_end_ms": elapsed,
    }


def _shuffle_graph_paths(records: list[dict[str, Any]], seed: int = 20260820) -> None:
    """Negative control: reassign each case's paths to a different case.

    If graph-path accuracy survives this, the metric is not measuring linking.
    """

    rng = random.Random(seed)
    paths = [record["graph_paths"] for record in records]
    rng.shuffle(paths)
    for record, shuffled in zip(records, paths, strict=True):
        record["graph_paths"] = shuffled


async def run(
    cases: tuple[EvaluationCase, ...],
    output_dir: Path,
    concurrency: int,
    *,
    shuffle_graph: bool,
) -> dict[str, Any]:
    database_url = os.getenv("DATABASE_URL", "")
    if not database_url.startswith(("postgres://", "postgresql://")):
        raise RuntimeError("DATABASE_URL must point to PostgreSQL")
    pool = ConnectionPool(
        database_url,
        min_size=1,
        max_size=max(2, concurrency),
        kwargs={"row_factory": dict_row},
    )
    service = QdrantGraphRetrieval(
        GraphRepository(pool.connection),
        QdrantProjectionRepository(pool.connection),
        _UnavailableFallback(),
        config=ProjectionConfig.from_env(),
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    arms: list[dict[str, Any]] = []
    try:
        semaphore = asyncio.Semaphore(concurrency)
        for arm in ARMS:
            records = list(
                await asyncio.gather(
                    *(_run_case(service, case, arm, semaphore) for case in cases)
                )
            )
            records.sort(key=lambda item: item["case_id"])
            if shuffle_graph:
                _shuffle_graph_paths(records)
            for record in records:
                RunRecord.from_dict(record)
            run_path = output_dir / f"ablation-{arm['id']}.v1.jsonl"
            run_path.write_text(
                "".join(
                    json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
                    for record in records
                ),
                encoding="utf-8",
            )
            report = EvaluationHarness(cases, top_k=10).score(
                [RunRecord.from_dict(record) for record in records],
                f"ablation_{arm['id']}",
            )
            arms.append(
                {
                    "id": arm["id"],
                    "label": arm["label"],
                    "route": arm["route"],
                    "graph_hops": arm["graph_hops"],
                    "runs_file": run_path.name,
                    "retrieval": report["metrics"]["retrieval"],
                    "graph": report["metrics"]["graph"],
                    "efficiency": {
                        key: report["metrics"]["efficiency"][key]
                        for key in ("end_to_end_p50_ms", "end_to_end_p95_ms")
                    },
                }
            )
    finally:
        await service.close()
        pool.close()

    by_id = {arm["id"]: arm for arm in arms}
    graph_delta = {
        metric: round(
            (by_id["hybrid_graph"]["retrieval"][metric] or 0.0)
            - (by_id["contextual_hybrid"]["retrieval"][metric] or 0.0),
            6,
        )
        for metric in ("recall_at_k", "ndcg_at_k", "mrr_at_k")
    }
    return {
        "schema_version": "raise.eval.ablation-report.v1",
        "case_count": len(cases),
        "negative_control_shuffled_graph": shuffle_graph,
        "arms": arms,
        # The number that answers "does the graph earn its place".
        "graph_contribution_over_contextual_hybrid": graph_delta,
        "scope": {
            "kind": "retrieval_only",
            "does_not_measure": [
                "answer_generation",
                "verifier_enforcement",
                "human_preference",
                "frontier_model_comparison",
            ],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cases", type=Path, default=Path("evaluation/golden/public_dev.v1.jsonl")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("build-reports/evaluation")
    )
    parser.add_argument("--concurrency", type=int, default=8)
    parser.add_argument(
        "--shuffle-graph",
        action="store_true",
        help="negative control: shuffle graph paths across cases before scoring",
    )
    args = parser.parse_args()

    cases = load_cases(args.cases)
    report = asyncio.run(
        run(
            cases,
            args.output,
            max(1, args.concurrency),
            shuffle_graph=args.shuffle_graph,
        )
    )
    name = "ablations.shuffled" if args.shuffle_graph else "ablations"
    target = args.output / f"{name}.report.v1.json"
    target.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps(report["graph_contribution_over_contextual_hybrid"], sort_keys=True))
    for arm in report["arms"]:
        retrieval = arm["retrieval"]
        print(
            f"{arm['id']:<20} recall@10={retrieval['recall_at_k']:.4f} "
            f"ndcg@10={retrieval['ndcg_at_k']:.4f} "
            f"graph_path={arm['graph']['path_accuracy']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
