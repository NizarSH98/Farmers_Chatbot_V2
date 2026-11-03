from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.evaluation.schema import (
    CASE_SCHEMA_VERSION,
    EvaluationCase,
    RunRecord,
    SchemaError,
    load_ablation_manifest,
    load_cases,
    load_pairwise_judgments,
    load_run_records,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "evaluation" / "fixtures"


def test_versioned_public_fixtures_load() -> None:
    cases = load_cases(FIXTURES / "public_cases.v1.jsonl")
    records = load_run_records(FIXTURES / "example_run.v1.jsonl")
    judgments = load_pairwise_judgments(FIXTURES / "example_pairwise.v1.jsonl")

    assert len(cases) == 2
    assert {case.language_group for case in cases} == {"arabic", "english"}
    assert all(case.fixture_only for case in cases)
    assert len(records) == 2
    assert len(judgments) == 4


def test_case_rejects_wrong_schema_and_duplicate_evidence() -> None:
    raw = {
        "schema_version": CASE_SCHEMA_VERSION,
        "case_id": "case-1",
        "split": "public_dev",
        "language": "en",
        "language_group": "english",
        "prompt": "Synthetic prompt",
        "relevant_evidence": [
            {"evidence_id": "same", "relevance": 3},
            {"evidence_id": "same", "relevance": 1},
        ],
        "expected_graph_paths": [],
        "claims": [],
        "risk": {"level": "low", "must_escalate": False, "prohibited_actions": []},
        "tags": [],
    }

    with pytest.raises(SchemaError, match="duplicate evidence"):
        EvaluationCase.from_dict(raw)
    raw["schema_version"] = "unknown"
    with pytest.raises(SchemaError, match="schema_version"):
        EvaluationCase.from_dict(raw)


def test_schema_rejects_unknown_and_missing_fields() -> None:
    raw = json.loads((FIXTURES / "public_cases.v1.jsonl").read_text().splitlines()[0])
    raw["unexpected"] = True
    with pytest.raises(SchemaError, match="unknown fields"):
        EvaluationCase.from_dict(raw)
    raw.pop("unexpected")
    raw.pop("risk")
    with pytest.raises(SchemaError, match="missing required"):
        EvaluationCase.from_dict(raw)


def test_run_rejects_duplicate_citation_pairs_and_invalid_scores() -> None:
    raw = json.loads((FIXTURES / "example_run.v1.jsonl").read_text().splitlines()[0])
    raw["citations"].append(dict(raw["citations"][0]))
    with pytest.raises(SchemaError, match="duplicate claim/evidence"):
        RunRecord.from_dict(raw)
    raw["citations"] = []
    raw["quality_score"] = 1.1
    with pytest.raises(SchemaError, match="quality_score"):
        RunRecord.from_dict(raw)
    raw["quality_score"] = float("nan")
    with pytest.raises(SchemaError, match="finite"):
        RunRecord.from_dict(raw)


def test_pairwise_loader_rejects_duplicate_reviewer_pair(tmp_path: Path) -> None:
    source = (FIXTURES / "example_pairwise.v1.jsonl").read_text().splitlines()[0]
    path = tmp_path / "duplicates.jsonl"
    path.write_text(source + "\n" + source + "\n", encoding="utf-8")

    with pytest.raises(SchemaError, match="duplicate records"):
        load_pairwise_judgments(path)


def test_machine_readable_schemas_and_ablation_ids_are_valid_json() -> None:
    schemas = ROOT / "evaluation" / "schema"
    for path in sorted(schemas.glob("*.json")):
        parsed = json.loads(path.read_text(encoding="utf-8"))
        assert parsed["$schema"].endswith("2020-12/schema")
        assert parsed["$id"].startswith("raise.eval.")
    manifest = json.loads(
        (ROOT / "evaluation" / "ablations.v1.json").read_text(encoding="utf-8")
    )
    identifiers = [item["id"] for item in manifest["definitions"]]
    assert len(identifiers) == len(set(identifiers))
    assert {"legacy_tfidf", "hybrid_graph", "full_raise"} <= set(identifiers)
    assert load_ablation_manifest(ROOT / "evaluation" / "ablations.v1.json")
