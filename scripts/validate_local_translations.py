"""Validate the v0.3 Arabic companion locally without external model calls."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from jsonschema import validate

from farmers_chatbot.knowledge_markdown import parse_knowledge_markdown
from farmers_chatbot.local_models import (
    TRANSLATION_REVIEW_SCHEMA,
    StructuredLocalModel,
)

VALIDATOR_VERSION = "raise-translation-validation-v2"
ENGLISH_SECTIONS = (
    "English guidance",
    "Decision logic",
    "Safe next action",
    "Avoid or escalate",
    "Evidence and applicability limits",
)


@dataclass(frozen=True)
class ArabicViewRecord:
    heading: str
    metadata: dict[str, Any]
    sections: tuple[str, ...]


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _arabic_records(path: Path) -> dict[str, ArabicViewRecord]:
    text = path.read_text(encoding="utf-8")
    if "\ufffd" in text:
        raise ValueError("Arabic companion contains a replacement character")
    headings = list(re.finditer(r"(?m)^## (.+?)\r?$", text))
    records: dict[str, ArabicViewRecord] = {}
    for index, heading in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        body = text[heading.end() : end]
        metadata_match = re.match(
            r"\s*(?:```|~~~)yaml\r?\n(.*?)\r?\n(?:```|~~~)",
            body,
            flags=re.DOTALL,
        )
        if not metadata_match:
            raise ValueError(f"Arabic metadata must follow heading: {heading.group(1)}")
        metadata = json.loads(metadata_match.group(1))
        section_matches = list(
            re.finditer(r"(?m)^### (.+?)\r?$", body[metadata_match.end() :])
        )
        section_body = body[metadata_match.end() :]
        sections: list[str] = []
        for section_index, section in enumerate(section_matches):
            section_end = (
                section_matches[section_index + 1].start()
                if section_index + 1 < len(section_matches)
                else len(section_body)
            )
            sections.append(section_body[section.end() : section_end].strip())
        record_id = str(metadata.get("id") or "")
        if not record_id or record_id in records:
            raise ValueError("Arabic companion record IDs must be unique and non-empty")
        if len(sections) < 5:
            raise ValueError(f"Arabic record {record_id} has fewer than five guidance sections")
        records[record_id] = ArabicViewRecord(
            heading=heading.group(1).strip(),
            metadata=metadata,
            sections=tuple(sections[:5]),
        )
    if not records:
        raise ValueError("Arabic companion contains no records")
    return records


def _compact(labelled: list[tuple[str, str]], *, per_section: int = 430) -> str:
    return "\n\n".join(
        f"[{label}]\n{text.strip()[:per_section]}" for label, text in labelled
    )


def _lineage_fields(metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        key: metadata.get(key)
        for key in (
            "id",
            "claim_ids",
            "source_ids",
            "ontology_version",
            "ontology_entities",
            "ontology_relations",
            "graph_relations",
            "geography",
            "risk",
            "review_status",
            "publication_scope",
        )
    }


def run(
    english_path: Path,
    arabic_path: Path,
    output_path: Path,
    *,
    require_all_pass: bool,
) -> dict[str, Any]:
    english = parse_knowledge_markdown(english_path)
    arabic = _arabic_records(arabic_path)
    english_by_id = {str(record.metadata["id"]): record for record in english.records}
    if set(english_by_id) != set(arabic):
        raise ValueError("English and Arabic knowledge ID sets differ")

    model = StructuredLocalModel()
    results: list[dict[str, Any]] = []
    for record_id in sorted(english_by_id):
        source = english_by_id[record_id]
        translated = arabic[record_id]
        if _lineage_fields(source.metadata) != _lineage_fields(translated.metadata):
            raise ValueError(f"Bilingual graph lineage differs for {record_id}")
        english_excerpt = _compact(
            [(name, source.sections[name]) for name in ENGLISH_SECTIONS]
        )
        arabic_excerpt = _compact(
            [(f"section-{index + 1}", value) for index, value in enumerate(translated.sections)]
        )
        pair_hash = _sha256(
            (VALIDATOR_VERSION + "\0" + english_excerpt + "\0" + arabic_excerpt).encode(
                "utf-8"
            )
        )
        review = model.review_translation(
            record_id=record_id,
            english=english_excerpt,
            arabic=arabic_excerpt,
            source_hash=pair_hash,
        )
        critic = model.review_translation(
            record_id=record_id,
            english=english_excerpt,
            arabic=arabic_excerpt,
            source_hash=pair_hash,
            critic=True,
        )
        validate(instance=review, schema=TRANSLATION_REVIEW_SCHEMA)
        validate(instance=critic, schema=TRANSLATION_REVIEW_SCHEMA)
        checks = (review, critic)
        passed = all(
            item["faithful"]
            and item["arabic_is_readable"]
            and item["safety_meaning_preserved"]
            and not item["material_omissions"]
            for item in checks
        )
        results.append(
            {
                "record_id": record_id,
                "pair_sha256": pair_hash,
                "passed": passed,
                "review": review,
                "critic": critic,
            }
        )

    report: dict[str, Any] = {
        "schema_version": VALIDATOR_VERSION,
        "english_path": english_path.as_posix(),
        "arabic_path": arabic_path.as_posix(),
        "english_sha256": _sha256(english_path.read_bytes()),
        "arabic_sha256": _sha256(arabic_path.read_bytes()),
        "model": asdict(model.config) | {"cache_dir": str(model.config.cache_dir)},
        "records": len(results),
        "passed": sum(bool(item["passed"]) for item in results),
        "failed": sum(not bool(item["passed"]) for item in results),
        "local_model_calls": model.calls,
        "cache_hits": model.cache_hits,
        "results": results,
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
    from scripts.translation_validation_v2 import run as complete_run

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--english",
        type=Path,
        default=Path("knowledge_base/agrifood_knowledge_v0.3.en.md"),
    )
    parser.add_argument(
        "--arabic",
        type=Path,
        default=Path("knowledge_base/agrifood_knowledge_v0.3.ar.md"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("build-reports/translation-validation.v0.3.json"),
    )
    parser.add_argument("--require-all-pass", action="store_true")
    args = parser.parse_args()
    report = complete_run(
        args.english,
        args.arabic,
        args.output,
        require_all_pass=args.require_all_pass,
    )
    print(
        json.dumps(
            {key: report[key] for key in ("records", "passed", "failed", "local_model_calls", "cache_hits", "report_sha256")},
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
