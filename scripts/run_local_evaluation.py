"""Run the active local Qdrant retrieval over the source-anchored evaluation."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import sys
import time
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
from farmers_chatbot.retrieval import EvidenceBundle, RetrievalRequest, RetrievalService
from scripts.evaluation.harness import EvaluationHarness
from scripts.evaluation.schema import (
    EvaluationCase,
    RunRecord,
    load_cases,
    load_run_records,
)


class _UnavailableFallback(RetrievalService):
    async def retrieve(
        self,
        request: RetrievalRequest,
        *,
        project_chunks: list[dict[str, Any]] | None = None,
    ) -> EvidenceBundle:
        return EvidenceBundle(
            warnings=["Qdrant was unavailable during the retrieval evaluation."],
            retrieval_metrics={"backend": "unavailable"},
        )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _mode(case: EvaluationCase) -> tuple[str, int]:
    tags = set(case.tags)
    if "multi_hop_graph" in tags:
        return "deep", 2
    if tags & {"actionable_decision", "troubleshooting", "safety_currentness"}:
        return "standard", 1
    return "quick", 0


async def _run_case(
    service: QdrantGraphRetrieval,
    case: EvaluationCase,
    semaphore: asyncio.Semaphore,
) -> dict[str, Any]:
    mode, graph_hops = _mode(case)
    language = "en" if case.language == "en" else "ar"
    async with semaphore:
        started = time.perf_counter()
        bundle = await service.retrieve(
            RetrievalRequest(
                query=case.prompt,
                language=language,
                mode=mode,
                geography="Akkar",
                risk=case.risk.level,
                currentness=("current" if "safety_currentness" in case.tags else "stable"),
                top_k=10,
                graph_hops=graph_hops,
            )
        )
    elapsed = (time.perf_counter() - started) * 1000
    evidence_items = sorted(
        [*bundle.passages, *bundle.claims],
        key=lambda item: float(item.scores.get("rrf") or item.scores.get("qdrant") or 0.0),
        reverse=True,
    )
    evidence_ids = list(dict.fromkeys(item.evidence_id for item in evidence_items))
    candidate_paths = [
        list(path)
        for path in dict.fromkeys(
            (
                str(item.get("subject_entity_id") or "unknown"),
                str(item.get("predicate") or "related_to"),
                str(item.get("object_entity_id") or item.get("object_text") or "context"),
            )
            for item in bundle.graph_paths
        )
    ]
    return {
        "schema_version": "raise.eval.run.v1",
        "case_id": case.case_id,
        "system_id": "qdrant_lazy_graphrag_retrieval",
        "retrieved_evidence_ids": evidence_ids,
        "graph_paths": candidate_paths,
        "citations": [],
        "escalated": False,
        "critical_violation": False,
        "unsafe_actions": [],
        "quality_score": None,
        "success": bundle.retrieval_metrics.get("backend") == "qdrant_lazy_graphrag",
        "cost_usd": 0.0,
        "ttft_ms": None,
        "end_to_end_ms": elapsed,
    }


async def run(cases: tuple[EvaluationCase, ...], output: Path, concurrency: int) -> dict[str, Any]:
    database_url = os.getenv("DATABASE_URL", "")
    if not database_url.startswith(("postgres://", "postgresql://")):
        raise RuntimeError("DATABASE_URL must point to PostgreSQL")
    pool = ConnectionPool(database_url, min_size=1, max_size=max(2, concurrency), kwargs={"row_factory": dict_row})
    service = QdrantGraphRetrieval(
        GraphRepository(pool.connection),
        QdrantProjectionRepository(pool.connection),
        _UnavailableFallback(),
        config=ProjectionConfig.from_env(),
    )
    try:
        semaphore = asyncio.Semaphore(concurrency)
        records = await asyncio.gather(
            *(_run_case(service, case, semaphore) for case in cases)
        )
    finally:
        await service.close()
        pool.close()
    records.sort(key=lambda item: item["case_id"])
    for record in records:
        RunRecord.from_dict(record)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )
    parsed = load_run_records(output)
    report = EvaluationHarness(cases, top_k=10).score(
        parsed, "qdrant_lazy_graphrag_retrieval"
    )
    # Retrieval cannot judge generated answers, entailment, or safety. Keep the
    # generic run schema, but do not publish its default values as measurements.
    for metric in ("quality", "citations", "safety"):
        report["metrics"].pop(metric, None)
    report["retrieval_by_language"] = retrieval_by_language(cases, report)
    report["scope"] = {
        "kind": "retrieval_only",
        "does_not_measure": [
            "answer_generation",
            "answer_quality",
            "citation_entailment",
            "safety",
            "verifier_enforcement",
            "human_preference",
            "frontier_model_comparison",
        ],
        "safety_escalation_not_applicable": True,
    }
    report["inputs"] = {
        "cases": len(cases),
        "runs_sha256": _sha256(output),
    }
    return report


def retrieval_by_language(
    cases: tuple[EvaluationCase, ...], report: dict[str, Any]
) -> dict[str, float | None]:
    groups: dict[str, list[float]] = {}
    cases_by_id = {case.case_id: case for case in cases}
    for result in report["cases"]:
        recall = result["retrieval_recall_at_k"]
        if recall is not None:
            group = cases_by_id[result["case_id"]].language_group
            groups.setdefault(group, []).append(float(recall))
    means = {group: sum(values) / len(values) for group, values in groups.items()}
    arabic, english = means.get("arabic"), means.get("english")
    return {
        **means,
        "arabic_deficit_points": (
            None if arabic is None or english is None
            else max(0.0, english - arabic) * 100
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=("public", "hidden"), default="public")
    parser.add_argument(
        "--max-language-gap-points",
        type=float,
        default=2.0,
        help=(
            "fail when Arabic retrieval recall trails English by more than this many points. "
            "RAISE is Arabic-first, so an English-first workflow must not be "
            "allowed to become English-only."
        ),
    )
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    cases_path = Path("evaluation/golden/public_dev.v1.jsonl") if args.split == "public" else Path("evaluation/hidden/acceptance.v1.jsonl")
    output = args.output or Path(f"build-reports/evaluation/qdrant_{args.split}.v1.jsonl")
    report_path = args.report or Path(f"build-reports/evaluation/qdrant_{args.split}.report.v1.json")
    cases = load_cases(cases_path)
    report = asyncio.run(run(cases, output, max(1, min(args.concurrency, 8))))
    report["dataset"] = {
        "split": args.split,
        "cases_sha256": _sha256(cases_path),
        "cases": len(cases),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"cases": len(cases), "runs": str(output), "report": str(report_path), "metrics": report.get("metrics")}, ensure_ascii=False, sort_keys=True))

    if report["metrics"]["efficiency"]["success_rate"] != 1.0:
        print("Retrieval evaluation failed: one or more cases used an unavailable backend.", file=sys.stderr)
        return 1
    gap = report["retrieval_by_language"]["arabic_deficit_points"]
    if gap is not None and gap > args.max_language_gap_points:
        print(
            f"language gap {gap:.3f} points exceeds the "
            f"{args.max_language_gap_points:.3f} limit",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
