from __future__ import annotations

import asyncio
from dataclasses import replace
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest
from conftest import _prepare

from farmers_chatbot.graph_repository import GraphRepository
from farmers_chatbot.qdrant_retrieval import QdrantGraphRetrieval
from farmers_chatbot.retrieval import EvidenceBundle, RetrievalRequest
from scripts.evaluation.schema import load_cases
from scripts.run_ablations import ARMS
from scripts.run_ablations import _run_case as run_ablation_case
from scripts.run_local_evaluation import _run_case, retrieval_by_language
from scripts.verify_backend import result_counts


def test_fixture_rejects_application_database_before_connecting() -> None:
    with pytest.raises(ValueError, match="Destructive test fixtures"):
        _prepare("postgresql://user:pass@127.0.0.1/raise")
    with pytest.raises(ValueError, match="Destructive test fixtures"):
        _prepare("postgresql://user:pass@remote.example/raise_test")


def test_release_evidence_counts_skipped_tests(tmp_path: Path) -> None:
    report = tmp_path / "results.xml"
    report.write_text(
        '<testsuites><testsuite tests="3" failures="0" errors="0" skipped="2"/>'
        '</testsuites>', encoding="utf-8",
    )
    assert result_counts(report) == {"tests": 3, "failures": 0, "errors": 0, "skipped": 2}


@pytest.mark.asyncio
@pytest.mark.parametrize("route", ["vector", "contextual", "lazy_graph"])
async def test_zero_hop_requests_do_not_touch_graph_services(route: str) -> None:
    service = object.__new__(QdrantGraphRetrieval)
    service._hybrid_points = AsyncMock(side_effect=AssertionError("graph lookup"))
    service.repository = Mock()
    request = RetrievalRequest(query="potato irrigation", language="en", mode="standard", graph_hops=0)
    assert await service._query_graph(request, "release", {}, route) == []
    service._hybrid_points.assert_not_called()
    service.repository.graph_paths.assert_not_called()
    factory = Mock(side_effect=AssertionError("database connection"))
    repository = GraphRepository(factory)
    assert repository.graph_paths(
        release_id="release", entity_ids=("potato",), max_hops=0,
        review_statuses=("approved",),
    ) == []
    factory.assert_not_called()


@pytest.mark.asyncio
async def test_retrieval_runners_do_not_invent_answer_judgments() -> None:
    case = load_cases(Path("evaluation/fixtures/public_cases.v1.jsonl"))[0]
    paths = [
        {"subject_entity_id": "a", "predicate": "relates", "object_entity_id": str(i)}
        for i in range(len(case.expected_graph_paths) + 3)
    ]
    service = Mock()
    service.retrieve = AsyncMock(return_value=EvidenceBundle(
        graph_paths=paths, retrieval_metrics={"backend": "unavailable"},
    ))
    records = [
        await _run_case(service, case, asyncio.Semaphore(1)),
        await run_ablation_case(service, case, ARMS[1], asyncio.Semaphore(1)),
    ]
    for record in records:
        assert not record["success"]
        assert record["quality_score"] is None
        assert record["citations"] == []
        assert len(record["graph_paths"]) == len(paths)


def test_language_gate_measures_arabic_recall_deficit_only() -> None:
    base = load_cases(Path("evaluation/fixtures/public_cases.v1.jsonl"))[0]
    cases = (
        replace(base, case_id="ar", language="ar", language_group="arabic"),
        replace(base, case_id="en", language="en", language_group="english"),
    )
    report = {"cases": [
        {"case_id": "ar", "retrieval_recall_at_k": 0.9},
        {"case_id": "en", "retrieval_recall_at_k": 0.6},
    ]}
    assert retrieval_by_language(cases, report)["arabic_deficit_points"] == 0
    report["cases"][0]["retrieval_recall_at_k"] = 0.4
    assert retrieval_by_language(cases, report)["arabic_deficit_points"] == pytest.approx(20)
