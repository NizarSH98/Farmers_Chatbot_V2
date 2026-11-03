"""Fail-closed validation for bilingual embedding benchmark approvals."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "raise.embedding_benchmark.v1"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class EmbeddingApprovalError(ValueError):
    """Raised when vector retrieval lacks a valid benchmark approval."""


@dataclass(frozen=True)
class EmbeddingApproval:
    model: str
    dimensions: int
    candidate_id: str
    report_sha256: str
    cases_sha256: str
    corpus_sha256: str
    candidates_sha256: str


def _number(item: dict[str, Any], key: str, *, default: float) -> float:
    try:
        value = float(item.get(key, default))
    except (TypeError, ValueError) as exc:
        raise EmbeddingApprovalError(f"Embedding result has invalid {key}") from exc
    if not math.isfinite(value):
        raise EmbeddingApprovalError(f"Embedding result has invalid {key}")
    return value


def _eligible(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scored = [
        item
        for item in results
        if isinstance(item, dict) and item.get("ndcg_at_10") is not None
    ]
    if not scored:
        return []
    best_ndcg = max(_number(item, "ndcg_at_10", default=-1) for item in scored)
    return [
        item
        for item in scored
        if _number(item, "recall_at_10", default=0) >= 0.90
        and _number(item, "language_gap", default=1) < 0.05
        and _number(item, "retrieval_p95_ms", default=math.inf) < 300
        and _number(item, "ndcg_at_10", default=-1) >= best_ndcg - 0.01
    ]


def load_embedding_approval(
    path: str | Path,
    *,
    expected_sha256: str | None = None,
) -> EmbeddingApproval:
    """Validate the report, hard gates, and deterministic candidate selection."""

    report_path = Path(path)
    try:
        raw_bytes = report_path.read_bytes()
        report = json.loads(raw_bytes.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EmbeddingApprovalError(
            "Embedding benchmark report is unreadable or invalid JSON"
        ) from exc
    report_hash = hashlib.sha256(raw_bytes).hexdigest()
    if expected_sha256 and report_hash != expected_sha256.lower():
        raise EmbeddingApprovalError("Embedding benchmark report checksum mismatch")
    if report.get("schema_version") != SCHEMA_VERSION:
        raise EmbeddingApprovalError("Unsupported embedding benchmark report")
    if report.get("vector_cutover_allowed") is not True:
        raise EmbeddingApprovalError("Embedding benchmark did not approve vector cutover")

    results = report.get("results")
    if not isinstance(results, list):
        raise EmbeddingApprovalError("Embedding benchmark results are missing")
    eligible = _eligible(results)
    if not eligible:
        raise EmbeddingApprovalError("No embedding candidate passes every hard gate")
    selected = str(report.get("selected") or "")
    expected = min(
        eligible,
        key=lambda item: (
            _number(item, "estimated_cost_usd", default=math.inf),
            -_number(item, "ndcg_at_10", default=-1),
            str(item.get("candidate_id") or ""),
        ),
    )
    if selected != str(expected.get("candidate_id") or ""):
        raise EmbeddingApprovalError(
            "Selected embedding is not the lowest-cost eligible candidate"
        )
    try:
        model = str(expected["model"]).strip()
        dimensions = int(expected["dimensions"])
    except (KeyError, TypeError, ValueError) as exc:
        raise EmbeddingApprovalError(
            "Selected embedding model or dimensions are invalid"
        ) from exc
    if not model or dimensions not in {768, 1536}:
        raise EmbeddingApprovalError(
            "Selected embedding must use a supported 768 or 1536 dimension index"
        )
    if selected != f"{model}@{dimensions}":
        raise EmbeddingApprovalError("Selected embedding candidate ID is inconsistent")

    hashes: dict[str, str] = {}
    for key in ("cases_sha256", "corpus_sha256", "candidates_sha256"):
        value = str(report.get(key) or "").lower()
        if not _SHA256.fullmatch(value):
            raise EmbeddingApprovalError(f"Embedding report has invalid {key}")
        hashes[key] = value
    return EmbeddingApproval(
        model=model,
        dimensions=dimensions,
        candidate_id=selected,
        report_sha256=report_hash,
        **hashes,
    )

