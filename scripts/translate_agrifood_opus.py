"""Generate the canonical complete Arabic asset with pinned local OPUS-MT."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
from pathlib import Path

from farmers_chatbot.knowledge_markdown import parse_knowledge_markdown
from farmers_chatbot.local_translation import (
    MODEL_ID,
    MODEL_REVISION,
    TRANSLATOR_VERSION,
    LocalArabicTranslator,
)
from scripts.translate_agrifood_local import OUTPUT_KEYS, _numbers, chunks
from scripts.translation_overrides import TRANSLATION_OVERRIDES

ASSET_VERSION = "raise-agrifood-arabic-v0.3-opus-mt-v2"
ARABIC_RE = re.compile(r"[\u0600-\u06ff]")
FOREIGN_RE = re.compile(r"[\u3400-\u9fff\uac00-\ud7af]")
SOURCE_REF_RE = re.compile(r"\[sources?:\s*[^\]]+\]", flags=re.IGNORECASE)


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def run(input_path: Path, output_path: Path) -> dict[str, object]:
    corpus = parse_knowledge_markdown(input_path)
    translator = LocalArabicTranslator()
    task_meta: list[tuple[str, str, str]] = []
    source_units: list[str] = []
    translation_inputs: list[str] = []
    source_refs: list[list[str]] = []
    for record in corpus.records:
        record_id = str(record.metadata["id"])
        for output_key, section_name in zip(
            OUTPUT_KEYS, list(record.sections)[::2][:5], strict=True
        ):
            for unit in chunks(record.sections[section_name]):
                task_meta.append((record_id, output_key, section_name))
                source_units.append(unit)
                references = SOURCE_REF_RE.findall(unit)
                source_refs.append(references)
                translation_inputs.append(SOURCE_REF_RE.sub("", unit).strip())
    translated_units = translator.translate_many(translation_inputs)
    nested: dict[str, dict[str, list[str]]] = {}
    unit_counters: dict[tuple[str, str], int] = {}
    for (record_id, output_key, section_name), source, translated, references in zip(
        task_meta, source_units, translated_units, source_refs, strict=True
    ):
        translated = f"{translated} {' '.join(references)}".strip()
        counter_key = (record_id, output_key)
        unit_counters[counter_key] = unit_counters.get(counter_key, 0) + 1
        translated = TRANSLATION_OVERRIDES.get(
            (record_id, output_key, unit_counters[counter_key]), translated
        )
        if not ARABIC_RE.search(translated) or FOREIGN_RE.search(translated):
            raise RuntimeError(
                f"invalid Arabic output for {record_id}/{section_name}"
            )
        missing_numbers = _numbers(source) - _numbers(translated)
        if missing_numbers:
            raise RuntimeError(
                f"translation lost numbers for {record_id}/{section_name}: {sorted(missing_numbers)}"
            )
        if len(translated) < max(2, int(len(source) * 0.20)):
            raise RuntimeError(
                f"translation is unexpectedly short for {record_id}/{section_name}"
            )
        nested.setdefault(record_id, {}).setdefault(output_key, []).append(translated)

    translations: dict[str, dict[str, str]] = {}
    for record in corpus.records:
        record_id = str(record.metadata["id"])
        translations[record_id] = {
            "title_ar": str(record.metadata["title_ar"]),
            **{
                output_key: "\n\n".join(nested[record_id][output_key])
                for output_key in OUTPUT_KEYS
            },
        }
    payload: dict[str, object] = {
        "schema_version": ASSET_VERSION,
        "translator_version": TRANSLATOR_VERSION,
        "source_path": input_path.as_posix(),
        "source_sha256": _sha256(input_path.read_bytes()),
        "model": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "records": len(translations),
        "chunks": len(source_units),
        "translations": translations,
        "translation_units": nested,
        "model_inputs": translator.inputs_translated,
        "cache_hits": translator.cache_hits,
        "batches": translator.batches,
    }
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    payload["asset_sha256"] = _sha256(canonical)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=output_path.parent,
        delete=False,
        newline="\n",
    ) as handle:
        handle.write(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        )
        temporary = Path(handle.name)
    temporary.replace(output_path)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("knowledge_base/agrifood_knowledge_v0.3.en.md"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("knowledge_base/agrifood_translations_v0.3.json"),
    )
    args = parser.parse_args()
    payload = run(args.input, args.output)
    print(
        json.dumps(
            {
                key: payload[key]
                for key in (
                    "records",
                    "chunks",
                    "model",
                    "model_revision",
                    "model_inputs",
                    "cache_hits",
                    "batches",
                    "asset_sha256",
                )
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
