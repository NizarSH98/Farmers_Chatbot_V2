"""Complete aligned-unit review for the local bilingual agrifood release."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from jsonschema import validate

from farmers_chatbot.knowledge_markdown import parse_knowledge_markdown
from farmers_chatbot.local_models import TRANSLATION_REVIEW_SCHEMA, StructuredLocalModel
from scripts.translate_agrifood_local import OUTPUT_KEYS, chunks
from scripts.validate_local_translations import _arabic_records, _lineage_fields

VALIDATOR_VERSION = "raise-translation-validation-v3-aligned-units"
MAX_PACK_CHARACTERS = 1800


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _packs(
    *,
    record_id: str,
    english_sections: list[tuple[str, str]],
    arabic_sections: tuple[str, ...],
    unit_map: dict[str, list[str]],
) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str, str]] = []
    for index, ((section_name, english), output_key, rendered_arabic) in enumerate(
        zip(english_sections, OUTPUT_KEYS, arabic_sections, strict=True),
        start=1,
    ):
        english_units = chunks(english)
        arabic_units = unit_map.get(output_key) or []
        if len(english_units) != len(arabic_units):
            raise ValueError(
                f"translation unit count differs for {record_id}/{section_name}"
            )
        if "\n\n".join(arabic_units).strip() != rendered_arabic.strip():
            raise ValueError(
                f"Arabic companion differs from translation asset for {record_id}/{section_name}"
            )
        for unit_index, (english_unit, arabic_unit) in enumerate(
            zip(english_units, arabic_units, strict=True),
            start=1,
        ):
            pairs.append(
                (
                    f"section-{index}-unit-{unit_index}",
                    english_unit.strip(),
                    str(arabic_unit).strip(),
                )
            )

    packs: list[tuple[str, str]] = []
    english_pack: list[str] = []
    arabic_pack: list[str] = []
    for label, english, arabic in pairs:
        english_item = f"[{label}]\n{english}"
        arabic_item = f"[{label}]\n{arabic}"
        candidate_en = "\n\n".join([*english_pack, english_item])
        candidate_ar = "\n\n".join([*arabic_pack, arabic_item])
        if english_pack and (
            len(candidate_en) > MAX_PACK_CHARACTERS
            or len(candidate_ar) > MAX_PACK_CHARACTERS
        ):
            packs.append(("\n\n".join(english_pack), "\n\n".join(arabic_pack)))
            english_pack = [english_item]
            arabic_pack = [arabic_item]
        else:
            english_pack.append(english_item)
            arabic_pack.append(arabic_item)
    if english_pack:
        packs.append(("\n\n".join(english_pack), "\n\n".join(arabic_pack)))
    return packs


def run(
    english_path: Path,
    arabic_path: Path,
    output_path: Path,
    *,
    require_all_pass: bool,
    translation_asset_path: Path = Path(
        "knowledge_base/agrifood_translations_v0.3.json"
    ),
) -> dict[str, Any]:
    english = parse_knowledge_markdown(english_path)
    arabic = _arabic_records(arabic_path)
    asset = json.loads(translation_asset_path.read_text(encoding="utf-8"))
    unit_maps = asset.get("translation_units") or {}
    english_by_id = {str(record.metadata["id"]): record for record in english.records}
    if set(english_by_id) != set(arabic) or set(english_by_id) != set(unit_maps):
        raise ValueError("English, Arabic, and translation-asset ID sets differ")

    model = StructuredLocalModel()
    results: list[dict[str, Any]] = []
    validation_units = 0
    validation_packs = 0
    for record_id in sorted(english_by_id):
        source = english_by_id[record_id]
        translated = arabic[record_id]
        if _lineage_fields(source.metadata) != _lineage_fields(translated.metadata):
            raise ValueError(f"Bilingual graph lineage differs for {record_id}")
        section_names = list(source.sections)[::2][:5]
        packs = _packs(
            record_id=record_id,
            english_sections=[(name, source.sections[name]) for name in section_names],
            arabic_sections=translated.sections,
            unit_map=unit_maps[record_id],
        )
        validation_units += sum(
            len(chunks(source.sections[name])) for name in section_names
        )
        pack_results: list[dict[str, Any]] = []
        for pack_index, (english_pack, arabic_pack) in enumerate(packs, start=1):
            pair_hash = _sha256(
                (
                    VALIDATOR_VERSION
                    + "\0"
                    + record_id
                    + "\0"
                    + english_pack
                    + "\0"
                    + arabic_pack
                ).encode("utf-8")
            )
            review = model.review_translation(
                record_id=f"{record_id}:pack-{pack_index}",
                english=english_pack,
                arabic=arabic_pack,
                source_hash=pair_hash,
            )
            critic = model.review_translation(
                record_id=f"{record_id}:pack-{pack_index}",
                english=english_pack,
                arabic=arabic_pack,
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
            pack_results.append(
                {
                    "pack": pack_index,
                    "pair_sha256": pair_hash,
                    "passed": passed,
                    "review": review,
                    "critic": critic,
                }
            )
        validation_packs += len(pack_results)
        results.append(
            {
                "record_id": record_id,
                "passed": all(item["passed"] for item in pack_results),
                "packs": pack_results,
            }
        )

    report: dict[str, Any] = {
        "schema_version": VALIDATOR_VERSION,
        "english_path": english_path.as_posix(),
        "arabic_path": arabic_path.as_posix(),
        "translation_asset_path": translation_asset_path.as_posix(),
        "english_sha256": _sha256(english_path.read_bytes()),
        "arabic_sha256": _sha256(arabic_path.read_bytes()),
        "translation_asset_sha256": _sha256(translation_asset_path.read_bytes()),
        "model": asdict(model.config) | {"cache_dir": str(model.config.cache_dir)},
        "records": len(results),
        "validation_units": validation_units,
        "validation_packs": validation_packs,
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
