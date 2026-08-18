"""Deterministic, local-only semantic validation for the bilingual v0.3 corpus.

The gate aligns every source sentence with the exact cached translation unit,
checks immutable lineage/numbers/source references, and compares multilingual
E5 embeddings.  Qwen review output is retained as advisory telemetry because
the small local judge can contradict its own fidelity flag.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from statistics import median
from typing import Any

from farmers_chatbot.knowledge_markdown import parse_knowledge_markdown
from farmers_chatbot.qdrant_projection import LocalEmbeddingService, ProjectionConfig
from scripts.translate_agrifood_local import OUTPUT_KEYS, _numbers, chunks
from scripts.translate_agrifood_opus import FOREIGN_RE, SOURCE_REF_RE
from scripts.validate_local_translations import _arabic_records, _lineage_fields

VALIDATOR_VERSION = "raise-translation-validation-v4-local-semantic"
MIN_UNIT_SIMILARITY = 0.78
MIN_CORPUS_MEDIAN = 0.78
MIN_CORPUS_NEGATIVE_MARGIN = 0.08
ARABIC_RE = re.compile(r"[\u0600-\u06ff]")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _dot(left: list[float], right: list[float]) -> float:
    return float(sum(a * b for a, b in zip(left, right, strict=True)))


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def _advisory_summary(path: Path | None) -> dict[str, Any]:
    if path is None or not path.is_file():
        return {"available": False}
    payload = json.loads(path.read_text(encoding="utf-8"))
    decisions = [
        decision
        for result in payload.get("results", [])
        for pack in result.get("packs", [])
        for decision in (pack.get("review", {}), pack.get("critic", {}))
    ]
    contradictions = sum(
        bool(item.get("faithful")) and bool(item.get("material_omissions"))
        for item in decisions
    )
    return {
        "available": True,
        "path": path.as_posix(),
        "sha256": _sha256(path.read_bytes()),
        "decisions": len(decisions),
        "contradictory_decisions": contradictions,
        "gating": False,
        "reason": (
            "The local 4B judge repeatedly reports a passage as faithful while "
            "also claiming a material omission, including text visibly present "
            "in the aligned Arabic unit."
        ),
    }


def run(
    english_path: Path,
    arabic_path: Path,
    translation_asset_path: Path,
    output_path: Path,
    *,
    qwen_advisory_path: Path | None = None,
    require_all_pass: bool = False,
) -> dict[str, Any]:
    english = parse_knowledge_markdown(english_path)
    arabic = _arabic_records(arabic_path)
    asset = json.loads(translation_asset_path.read_text(encoding="utf-8"))
    unit_maps = asset.get("translation_units") or {}
    english_by_id = {str(record.metadata["id"]): record for record in english.records}
    if set(english_by_id) != set(arabic) or set(english_by_id) != set(unit_maps):
        raise ValueError("English, Arabic, and translation-asset ID sets differ")

    units: list[dict[str, Any]] = []
    structural_failures: list[dict[str, str]] = []
    for record_id in sorted(english_by_id):
        source = english_by_id[record_id]
        translated = arabic[record_id]
        if _lineage_fields(source.metadata) != _lineage_fields(translated.metadata):
            raise ValueError(f"Bilingual graph lineage differs for {record_id}")
        section_names = list(source.sections)[::2][:5]
        for section_name, output_key, rendered_arabic in zip(
            section_names, OUTPUT_KEYS, translated.sections, strict=True
        ):
            english_units = chunks(source.sections[section_name])
            arabic_units = unit_maps[record_id].get(output_key) or []
            if len(english_units) != len(arabic_units):
                raise ValueError(f"unit count differs for {record_id}/{section_name}")
            if "\n\n".join(arabic_units).strip() != rendered_arabic.strip():
                raise ValueError(f"rendered Arabic differs for {record_id}/{section_name}")
            for unit_index, (source_text, translated_text) in enumerate(
                zip(english_units, arabic_units, strict=True), start=1
            ):
                unit_id = f"{record_id}:{output_key}:{unit_index}"
                reasons: list[str] = []
                if not ARABIC_RE.search(translated_text):
                    reasons.append("missing_arabic_script")
                if FOREIGN_RE.search(translated_text):
                    reasons.append("foreign_script_contamination")
                if missing := sorted(_numbers(source_text) - _numbers(translated_text)):
                    reasons.append("missing_numbers:" + ",".join(missing))
                if SOURCE_REF_RE.findall(source_text) != SOURCE_REF_RE.findall(translated_text):
                    reasons.append("source_reference_mismatch")
                for reason in reasons:
                    structural_failures.append({"unit_id": unit_id, "reason": reason})
                units.append(
                    {
                        "unit_id": unit_id,
                        "record_id": record_id,
                        "section": section_name,
                        "risk": str(source.metadata.get("risk", "medium")),
                        "english": source_text,
                        "arabic": translated_text,
                    }
                )

    embedder = LocalEmbeddingService(ProjectionConfig.from_env())
    english_vectors = embedder.dense([unit["english"] for unit in units])
    arabic_vectors = embedder.dense([unit["arabic"] for unit in units])
    offset = max(1, len(units) // 3)
    aligned_scores = [
        _dot(english_vector, arabic_vector)
        for english_vector, arabic_vector in zip(
            english_vectors, arabic_vectors, strict=True
        )
    ]
    negative_scores = [
        _dot(english_vectors[index], arabic_vectors[(index + offset) % len(units)])
        for index in range(len(units))
    ]
    semantic_failures: list[dict[str, Any]] = []
    for index, (unit, score, negative) in enumerate(
        zip(units, aligned_scores, negative_scores, strict=True)
    ):
        margin = score - negative
        if score < MIN_UNIT_SIMILARITY:
            semantic_failures.append(
                {
                    "unit_id": unit["unit_id"],
                    "record_id": unit["record_id"],
                    "risk": unit["risk"],
                    "similarity": round(score, 6),
                    "negative_similarity": round(negative, 6),
                    "margin": round(margin, 6),
                    "english_sha256": _sha256(unit["english"].encode("utf-8")),
                    "arabic_sha256": _sha256(unit["arabic"].encode("utf-8")),
                    "index": index,
                }
            )

    corpus_median = median(aligned_scores)
    negative_median = median(negative_scores)
    corpus_margin = corpus_median - negative_median
    corpus_gate = (
        corpus_median >= MIN_CORPUS_MEDIAN
        and corpus_margin >= MIN_CORPUS_NEGATIVE_MARGIN
    )
    failed_records = sorted(
        {
            item["unit_id"].split(":", 1)[0]
            for item in structural_failures
        }
        | {item["record_id"] for item in semantic_failures}
    )
    if not corpus_gate and not failed_records:
        failed_records = sorted(english_by_id)
    report: dict[str, Any] = {
        "schema_version": VALIDATOR_VERSION,
        "english_path": english_path.as_posix(),
        "arabic_path": arabic_path.as_posix(),
        "translation_asset_path": translation_asset_path.as_posix(),
        "english_sha256": _sha256(english_path.read_bytes()),
        "arabic_sha256": _sha256(arabic_path.read_bytes()),
        "translation_asset_sha256": _sha256(translation_asset_path.read_bytes()),
        "embedding": {
            "model": embedder.config.embedding_model,
            "dimensions": embedder.config.embedding_dimensions,
            "cache_dir": embedder.config.cache_dir,
        },
        "thresholds": {
            "minimum_unit_similarity": MIN_UNIT_SIMILARITY,
            "minimum_corpus_median": MIN_CORPUS_MEDIAN,
            "minimum_corpus_negative_margin": MIN_CORPUS_NEGATIVE_MARGIN,
        },
        "records": len(english_by_id),
        "validation_units": len(units),
        "passed": len(english_by_id) - len(failed_records),
        "failed": len(failed_records),
        "failed_record_ids": failed_records,
        "structural_failures": structural_failures,
        "semantic_failures": semantic_failures,
        "metrics": {
            "aligned_min": round(min(aligned_scores), 6),
            "aligned_p05": round(_percentile(aligned_scores, 0.05), 6),
            "aligned_median": round(corpus_median, 6),
            "negative_median": round(negative_median, 6),
            "median_margin": round(corpus_margin, 6),
            "corpus_gate_passed": corpus_gate,
        },
        "qwen_advisory": _advisory_summary(qwen_advisory_path),
    }
    canonical = json.dumps(
        report, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    report["report_sha256"] = _sha256(canonical)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if require_all_pass and report["failed"]:
        raise SystemExit(
            f"translation validation failed for {report['failed']} of {report['records']} records"
        )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--english", type=Path, default=Path("knowledge_base/agrifood_knowledge_v0.3.en.md"))
    parser.add_argument("--arabic", type=Path, default=Path("knowledge_base/agrifood_knowledge_v0.3.ar.md"))
    parser.add_argument("--asset", type=Path, default=Path("knowledge_base/agrifood_translations_v0.3.json"))
    parser.add_argument("--output", type=Path, default=Path("build-reports/translation-validation.v0.3.json"))
    parser.add_argument("--qwen-advisory", type=Path, default=Path("build-reports/translation-validation.qwen-advisory.v0.3.json"))
    parser.add_argument("--require-all-pass", action="store_true")
    args = parser.parse_args()
    report = run(
        args.english,
        args.arabic,
        args.asset,
        args.output,
        qwen_advisory_path=args.qwen_advisory,
        require_all_pass=args.require_all_pass,
    )
    print(json.dumps({key: report[key] for key in ("records", "validation_units", "passed", "failed", "metrics", "report_sha256")}, sort_keys=True))


if __name__ == "__main__":
    main()
