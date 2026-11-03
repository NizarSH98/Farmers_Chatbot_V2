from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from scripts.evaluation.cli import main
from scripts.evaluation.harness import EvaluationHarness
from scripts.evaluation.schema import (
    load_cases,
    load_pairwise_judgments,
    load_run_records,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "evaluation" / "fixtures"


def test_harness_scores_all_required_dimensions() -> None:
    cases = load_cases(FIXTURES / "public_cases.v1.jsonl")
    records = load_run_records(FIXTURES / "example_run.v1.jsonl")
    report = EvaluationHarness(cases, top_k=10).score(records, "example_system")
    metrics = report["metrics"]

    assert report["coverage"]["run_coverage"] == 1
    assert metrics["retrieval"]["recall_at_k"] == 0.5
    assert metrics["retrieval"]["mrr_at_k"] == 0.5
    assert metrics["retrieval"]["ndcg_at_k"] == 0.5
    assert metrics["graph"]["path_accuracy"] == 1
    assert metrics["citations"]["precision"] == 0.5
    assert metrics["citations"]["recall"] == 0.5
    assert metrics["safety"]["critical_unsafe_count"] == 0
    assert metrics["safety"]["escalation_recall"] == 1
    assert metrics["quality"]["arabic_english_gap_points"] == 10
    assert metrics["efficiency"]["total_cost_usd"] == 0.03
    assert metrics["efficiency"]["cost_per_success_usd"] == 0.015
    assert metrics["efficiency"]["ttft_p95_ms"] == 120
    assert metrics["efficiency"]["end_to_end_p95_ms"] == 600


def test_missing_run_records_reduce_coverage_and_success() -> None:
    cases = load_cases(FIXTURES / "public_cases.v1.jsonl")
    records = load_run_records(FIXTURES / "example_run.v1.jsonl")[:1]
    report = EvaluationHarness(cases).score(records, "example_system")

    assert report["coverage"]["run_coverage"] == 0.5
    assert report["metrics"]["efficiency"]["success_rate"] == 0.5
    assert report["metrics"]["quality"]["arabic_english_gap"] is None
    assert any(not item["record_present"] for item in report["cases"])


def test_prohibited_action_counts_as_critical_unsafe() -> None:
    cases = load_cases(FIXTURES / "public_cases.v1.jsonl")
    records = list(load_run_records(FIXTURES / "example_run.v1.jsonl"))
    records[0] = replace(records[0], unsafe_actions=("fixture-prohibited-action",))
    report = EvaluationHarness(cases).score(tuple(records), "example_system")

    assert report["metrics"]["safety"]["critical_unsafe_count"] == 1


def test_pairwise_fixture_has_seeded_case_cluster_interval() -> None:
    judgments = load_pairwise_judgments(FIXTURES / "example_pairwise.v1.jsonl")
    result = EvaluationHarness.score_pairwise(judgments, seed=22, resamples=300)

    assert result[0]["system_a"] == "example_baseline"
    assert result[0]["score_a"] == pytest.approx(0.375)
    assert result[0]["case_count"] == 2
    assert result[0]["judgment_count"] == 4


def test_cli_output_is_byte_reproducible(tmp_path: Path) -> None:
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    common = [
        "score",
        "--cases",
        str(FIXTURES / "public_cases.v1.jsonl"),
        "--runs",
        str(FIXTURES / "example_run.v1.jsonl"),
        "--pairwise",
        str(FIXTURES / "example_pairwise.v1.jsonl"),
        "--ablations",
        str(ROOT / "evaluation" / "ablations.v1.json"),
        "--system-id",
        "example_system",
        "--dataset-id",
        "synthetic-contract-fixture",
        "--dataset-version",
        "1",
        "--bootstrap-resamples",
        "200",
    ]
    assert main([*common, "--output", str(first)]) == 0
    assert main([*common, "--output", str(second)]) == 0

    assert first.read_bytes() == second.read_bytes()
    report = json.loads(first.read_text(encoding="utf-8"))
    assert report["dataset"]["cases_sha256"]
    assert report["ablation_manifest"]["sha256"]
