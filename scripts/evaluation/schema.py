"""Strict v1 schemas for evaluation cases, run outputs, and preferences."""

from __future__ import annotations

import json
import math
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CASE_SCHEMA_VERSION = "raise.eval.case.v1"
RUN_SCHEMA_VERSION = "raise.eval.run.v1"
PAIRWISE_SCHEMA_VERSION = "raise.eval.pairwise.v1"
ABLATION_SCHEMA_VERSION = "raise.eval.ablations.v1"


class SchemaError(ValueError):
    """Raised when an evaluation fixture violates its versioned contract."""


def _shape(
    value: dict[str, Any],
    field: str,
    *,
    required: set[str],
    optional: set[str] | None = None,
) -> None:
    allowed = required | (optional or set())
    unknown = sorted(set(value) - allowed)
    missing = sorted(required - set(value))
    if unknown:
        raise SchemaError(f"{field} contains unknown fields: {', '.join(unknown)}")
    if missing:
        raise SchemaError(f"{field} is missing required fields: {', '.join(missing)}")


def _object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SchemaError(f"{field} must be an object")
    return value


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SchemaError(f"{field} must be a non-empty string")
    return value.strip()


def _boolean(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise SchemaError(f"{field} must be a boolean")
    return value


def _number(value: Any, field: str, *, maximum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise SchemaError(f"{field} must be a number")
    result = float(value)
    if not math.isfinite(result):
        raise SchemaError(f"{field} must be finite")
    if result < 0 or (maximum is not None and result > maximum):
        suffix = f" and <= {maximum}" if maximum is not None else ""
        raise SchemaError(f"{field} must be >= 0{suffix}")
    return result


def _strings(value: Any, field: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise SchemaError(f"{field} must be an array")
    result = tuple(_string(item, f"{field}[]") for item in value)
    if len(result) != len(set(result)):
        raise SchemaError(f"{field} must not contain duplicates")
    return result


def _paths(value: Any, field: str) -> tuple[tuple[str, ...], ...]:
    if not isinstance(value, list):
        raise SchemaError(f"{field} must be an array")
    paths = tuple(_strings(item, f"{field}[]") for item in value)
    if any(len(path) < 2 for path in paths):
        raise SchemaError(f"{field} paths must contain at least two tokens")
    if len(paths) != len(set(paths)):
        raise SchemaError(f"{field} must not contain duplicate paths")
    return paths


@dataclass(frozen=True)
class EvidenceRelevance:
    evidence_id: str
    relevance: int

    @classmethod
    def from_dict(cls, raw: Any, field: str) -> EvidenceRelevance:
        value = _object(raw, field)
        _shape(value, field, required={"evidence_id", "relevance"})
        relevance = value.get("relevance")
        if isinstance(relevance, bool) or not isinstance(relevance, int):
            raise SchemaError(f"{field}.relevance must be an integer")
        if relevance < 1 or relevance > 3:
            raise SchemaError(f"{field}.relevance must be between 1 and 3")
        return cls(
            evidence_id=_string(value.get("evidence_id"), f"{field}.evidence_id"),
            relevance=relevance,
        )


@dataclass(frozen=True)
class ClaimExpectation:
    claim_id: str
    requires_citation: bool
    expected_evidence_ids: tuple[str, ...]

    @classmethod
    def from_dict(cls, raw: Any, field: str) -> ClaimExpectation:
        value = _object(raw, field)
        _shape(
            value,
            field,
            required={"claim_id", "requires_citation", "expected_evidence_ids"},
        )
        return cls(
            claim_id=_string(value.get("claim_id"), f"{field}.claim_id"),
            requires_citation=_boolean(
                value.get("requires_citation"), f"{field}.requires_citation"
            ),
            expected_evidence_ids=_strings(
                value.get("expected_evidence_ids", []),
                f"{field}.expected_evidence_ids",
            ),
        )


@dataclass(frozen=True)
class RiskExpectation:
    level: str
    must_escalate: bool
    prohibited_actions: tuple[str, ...]

    @classmethod
    def from_dict(cls, raw: Any, field: str) -> RiskExpectation:
        value = _object(raw, field)
        _shape(
            value,
            field,
            required={"level", "must_escalate", "prohibited_actions"},
        )
        level = _string(value.get("level"), f"{field}.level")
        if level not in {"low", "medium", "high", "critical"}:
            raise SchemaError(f"{field}.level is not supported")
        return cls(
            level=level,
            must_escalate=_boolean(
                value.get("must_escalate"), f"{field}.must_escalate"
            ),
            prohibited_actions=_strings(
                value.get("prohibited_actions", []),
                f"{field}.prohibited_actions",
            ),
        )


@dataclass(frozen=True)
class EvaluationCase:
    case_id: str
    split: str
    language: str
    language_group: str
    prompt: str
    relevant_evidence: tuple[EvidenceRelevance, ...]
    expected_graph_paths: tuple[tuple[str, ...], ...]
    claims: tuple[ClaimExpectation, ...]
    risk: RiskExpectation
    tags: tuple[str, ...]
    fixture_only: bool = False

    @classmethod
    def from_dict(cls, raw: Any) -> EvaluationCase:
        value = _object(raw, "case")
        _shape(
            value,
            "case",
            required={
                "schema_version",
                "case_id",
                "split",
                "language",
                "language_group",
                "prompt",
                "relevant_evidence",
                "expected_graph_paths",
                "claims",
                "risk",
                "tags",
            },
            optional={"fixture_only"},
        )
        if value.get("schema_version") != CASE_SCHEMA_VERSION:
            raise SchemaError(f"case.schema_version must be {CASE_SCHEMA_VERSION}")
        split = _string(value.get("split"), "case.split")
        if split not in {"public_dev", "hidden_test"}:
            raise SchemaError("case.split must be public_dev or hidden_test")
        language_group = _string(
            value.get("language_group"), "case.language_group"
        )
        if language_group not in {"arabic", "english", "other"}:
            raise SchemaError("case.language_group must be arabic, english, or other")
        evidence_raw = value.get("relevant_evidence", [])
        if not isinstance(evidence_raw, list):
            raise SchemaError("case.relevant_evidence must be an array")
        relevant = tuple(
            EvidenceRelevance.from_dict(item, f"case.relevant_evidence[{index}]")
            for index, item in enumerate(evidence_raw)
        )
        evidence_ids = [item.evidence_id for item in relevant]
        if len(evidence_ids) != len(set(evidence_ids)):
            raise SchemaError("case.relevant_evidence contains duplicate evidence IDs")
        claims_raw = value.get("claims", [])
        if not isinstance(claims_raw, list):
            raise SchemaError("case.claims must be an array")
        claims = tuple(
            ClaimExpectation.from_dict(item, f"case.claims[{index}]")
            for index, item in enumerate(claims_raw)
        )
        claim_ids = [item.claim_id for item in claims]
        if len(claim_ids) != len(set(claim_ids)):
            raise SchemaError("case.claims contains duplicate claim IDs")
        fixture_only = value.get("fixture_only", False)
        return cls(
            case_id=_string(value.get("case_id"), "case.case_id"),
            split=split,
            language=_string(value.get("language"), "case.language"),
            language_group=language_group,
            prompt=_string(value.get("prompt"), "case.prompt"),
            relevant_evidence=relevant,
            expected_graph_paths=_paths(
                value.get("expected_graph_paths", []),
                "case.expected_graph_paths",
            ),
            claims=claims,
            risk=RiskExpectation.from_dict(value.get("risk"), "case.risk"),
            tags=_strings(value.get("tags", []), "case.tags"),
            fixture_only=_boolean(fixture_only, "case.fixture_only"),
        )


@dataclass(frozen=True)
class CitationJudgment:
    claim_id: str
    evidence_id: str
    entails: bool

    @classmethod
    def from_dict(cls, raw: Any, field: str) -> CitationJudgment:
        value = _object(raw, field)
        _shape(
            value,
            field,
            required={"claim_id", "evidence_id", "entails"},
        )
        return cls(
            claim_id=_string(value.get("claim_id"), f"{field}.claim_id"),
            evidence_id=_string(value.get("evidence_id"), f"{field}.evidence_id"),
            entails=_boolean(value.get("entails"), f"{field}.entails"),
        )


@dataclass(frozen=True)
class RunRecord:
    case_id: str
    system_id: str
    retrieved_evidence_ids: tuple[str, ...]
    graph_paths: tuple[tuple[str, ...], ...]
    citations: tuple[CitationJudgment, ...]
    escalated: bool
    critical_violation: bool
    unsafe_actions: tuple[str, ...]
    quality_score: float | None
    success: bool
    cost_usd: float | None
    ttft_ms: float | None
    end_to_end_ms: float | None

    @classmethod
    def from_dict(cls, raw: Any) -> RunRecord:
        value = _object(raw, "run")
        _shape(
            value,
            "run",
            required={
                "schema_version",
                "case_id",
                "system_id",
                "retrieved_evidence_ids",
                "graph_paths",
                "citations",
                "escalated",
                "critical_violation",
                "unsafe_actions",
                "quality_score",
                "success",
                "cost_usd",
                "ttft_ms",
                "end_to_end_ms",
            },
        )
        if value.get("schema_version") != RUN_SCHEMA_VERSION:
            raise SchemaError(f"run.schema_version must be {RUN_SCHEMA_VERSION}")
        citations_raw = value.get("citations", [])
        if not isinstance(citations_raw, list):
            raise SchemaError("run.citations must be an array")
        citations = tuple(
            CitationJudgment.from_dict(item, f"run.citations[{index}]")
            for index, item in enumerate(citations_raw)
        )
        citation_pairs = [(item.claim_id, item.evidence_id) for item in citations]
        if len(citation_pairs) != len(set(citation_pairs)):
            raise SchemaError("run.citations contains duplicate claim/evidence pairs")
        quality_raw = value.get("quality_score")
        quality = (
            None
            if quality_raw is None
            else _number(quality_raw, "run.quality_score", maximum=1)
        )

        def optional_number(field: str) -> float | None:
            raw_value = value.get(field)
            return None if raw_value is None else _number(raw_value, f"run.{field}")

        return cls(
            case_id=_string(value.get("case_id"), "run.case_id"),
            system_id=_string(value.get("system_id"), "run.system_id"),
            retrieved_evidence_ids=_strings(
                value.get("retrieved_evidence_ids", []),
                "run.retrieved_evidence_ids",
            ),
            graph_paths=_paths(value.get("graph_paths", []), "run.graph_paths"),
            citations=citations,
            escalated=_boolean(value.get("escalated"), "run.escalated"),
            critical_violation=_boolean(
                value.get("critical_violation"), "run.critical_violation"
            ),
            unsafe_actions=_strings(
                value.get("unsafe_actions", []), "run.unsafe_actions"
            ),
            quality_score=quality,
            success=_boolean(value.get("success"), "run.success"),
            cost_usd=optional_number("cost_usd"),
            ttft_ms=optional_number("ttft_ms"),
            end_to_end_ms=optional_number("end_to_end_ms"),
        )


@dataclass(frozen=True)
class PairwiseJudgment:
    case_id: str
    system_a: str
    system_b: str
    winner: str
    judge_id: str

    @classmethod
    def from_dict(cls, raw: Any) -> PairwiseJudgment:
        value = _object(raw, "pairwise")
        _shape(
            value,
            "pairwise",
            required={
                "schema_version",
                "case_id",
                "system_a",
                "system_b",
                "winner",
                "judge_id",
            },
        )
        if value.get("schema_version") != PAIRWISE_SCHEMA_VERSION:
            raise SchemaError(
                f"pairwise.schema_version must be {PAIRWISE_SCHEMA_VERSION}"
            )
        system_a = _string(value.get("system_a"), "pairwise.system_a")
        system_b = _string(value.get("system_b"), "pairwise.system_b")
        if system_a == system_b:
            raise SchemaError("pairwise systems must differ")
        winner = _string(value.get("winner"), "pairwise.winner")
        if winner not in {"a", "b", "tie"}:
            raise SchemaError("pairwise.winner must be a, b, or tie")
        return cls(
            case_id=_string(value.get("case_id"), "pairwise.case_id"),
            system_a=system_a,
            system_b=system_b,
            winner=winner,
            judge_id=_string(value.get("judge_id"), "pairwise.judge_id"),
        )


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SchemaError(f"{path}:{line_number}: invalid JSON: {exc.msg}") from exc
        records.append(_object(value, f"{path}:{line_number}"))
    if not records:
        raise SchemaError(f"{path} contains no records")
    return records


def _unique(records: Iterable[Any], key: Any, label: str) -> tuple[Any, ...]:
    result = tuple(records)
    values = [key(item) for item in result]
    if len(values) != len(set(values)):
        raise SchemaError(f"{label} contains duplicate records")
    return result


def load_cases(path: Path) -> tuple[EvaluationCase, ...]:
    return _unique(
        (EvaluationCase.from_dict(item) for item in _read_jsonl(path)),
        lambda item: item.case_id,
        "case file",
    )


def load_run_records(path: Path) -> tuple[RunRecord, ...]:
    return _unique(
        (RunRecord.from_dict(item) for item in _read_jsonl(path)),
        lambda item: (item.system_id, item.case_id),
        "run file",
    )


def load_pairwise_judgments(path: Path) -> tuple[PairwiseJudgment, ...]:
    return _unique(
        (PairwiseJudgment.from_dict(item) for item in _read_jsonl(path)),
        lambda item: (
            item.case_id,
            min(item.system_a, item.system_b),
            max(item.system_a, item.system_b),
            item.judge_id,
        ),
        "pairwise file",
    )


def load_ablation_manifest(path: Path) -> dict[str, Any]:
    try:
        value = _object(json.loads(path.read_text(encoding="utf-8")), "ablations")
    except json.JSONDecodeError as exc:
        raise SchemaError(f"{path}: invalid JSON: {exc.msg}") from exc
    _shape(
        value,
        "ablations",
        required={"schema_version", "definitions"},
    )
    if value["schema_version"] != ABLATION_SCHEMA_VERSION:
        raise SchemaError(
            f"ablations.schema_version must be {ABLATION_SCHEMA_VERSION}"
        )
    definitions = value["definitions"]
    if not isinstance(definitions, list) or not definitions:
        raise SchemaError("ablations.definitions must be a non-empty array")
    identifiers: list[str] = []
    for index, raw in enumerate(definitions):
        field = f"ablations.definitions[{index}]"
        definition = _object(raw, field)
        _shape(
            definition,
            field,
            required={
                "id",
                "label",
                "lexical",
                "vector",
                "contextual_chunks",
                "graph_hops",
                "tools",
            },
        )
        identifiers.append(_string(definition["id"], f"{field}.id"))
        _string(definition["label"], f"{field}.label")
        for boolean_field in ("lexical", "vector", "contextual_chunks", "tools"):
            _boolean(definition[boolean_field], f"{field}.{boolean_field}")
        graph_hops = definition["graph_hops"]
        if (
            isinstance(graph_hops, bool)
            or not isinstance(graph_hops, int)
            or graph_hops < 0
            or graph_hops > 2
        ):
            raise SchemaError(f"{field}.graph_hops must be an integer from 0 to 2")
    if len(identifiers) != len(set(identifiers)):
        raise SchemaError("ablations.definitions contains duplicate IDs")
    return value
