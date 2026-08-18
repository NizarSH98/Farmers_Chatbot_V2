"""Create complete Arabic v0.3 translations with the pinned local Ollama model."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
from pathlib import Path

from farmers_chatbot.knowledge_markdown import parse_knowledge_markdown
from farmers_chatbot.local_models import StructuredLocalModel

TRANSLATION_ASSET_VERSION = "raise-agrifood-arabic-v0.3-translation-v1"
OUTPUT_KEYS = (
    "guidance_ar",
    "decision_logic_ar",
    "safe_next_action_ar",
    "avoid_escalate_ar",
    "applicability_limits_ar",
)
ARABIC_RE = re.compile(r"[\u0600-\u06ff]")
NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)?")
ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩٫٬", "0123456789.,")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _split_long(value: str, maximum: int) -> list[str]:
    sentences = re.split(r"(?<=[.!?;:])\s+", value)
    if len(sentences) == 1:
        return [value[index : index + maximum] for index in range(0, len(value), maximum)]
    result: list[str] = []
    current = ""
    for sentence in sentences:
        candidate = f"{current} {sentence}".strip()
        if current and len(candidate) > maximum:
            result.append(current)
            current = sentence
        else:
            current = candidate
    if current:
        result.append(current)
    return result


def chunks(value: str, *, maximum: int = 600) -> list[str]:
    units: list[str] = []
    for paragraph in (item.strip() for item in value.split("\n\n")):
        if not paragraph:
            continue
        sentences = [
            item.strip()
            for item in re.split(r"(?<=[.!?])\s+", paragraph)
            if item.strip()
        ]
        for sentence in sentences:
            units.extend(_split_long(sentence, maximum) if len(sentence) > maximum else [sentence])
    return units


def _numbers(value: str) -> set[str]:
    normalized = value.translate(ARABIC_DIGITS)
    normalized = re.sub(
        r"(?<!\d)000\s*,\s*(\d{1,3})(?!\d)",
        lambda match: f"{match.group(1)}000",
        normalized,
    )
    normalized = re.sub(
        r"(?<!\d)000\s+(\d{1,3})(?!\d)",
        lambda match: f"{match.group(1)}000",
        normalized,
    )
    normalized = re.sub(
        r"(?<!\d)(\d{3})\s+(\d{1,3})(?![\d.])",
        lambda match: f"{match.group(2)}{match.group(1)}",
        normalized,
    )
    return {item.replace(",", "") for item in NUMBER_RE.findall(normalized)}


def run(input_path: Path, output_path: Path) -> dict[str, object]:
    corpus = parse_knowledge_markdown(input_path)
    model = StructuredLocalModel()
    translations: dict[str, dict[str, str]] = {}
    total_chunks = 0
    translation_units: dict[str, dict[str, list[str]]] = {}
    for record_index, record in enumerate(corpus.records, start=1):
        record_id = str(record.metadata["id"])
        section_names = list(record.sections)
        translated_fields: dict[str, str] = {
            "title_ar": str(record.metadata["title_ar"])
        }
        record_units: dict[str, list[str]] = {}
        for output_key, section_name in zip(OUTPUT_KEYS, section_names[::2][:5], strict=True):
            source = record.sections[section_name]
            pieces: list[str] = []
            for chunk_index, chunk in enumerate(chunks(source)):
                chunk_hash = _sha256(
                    (TRANSLATION_ASSET_VERSION + "\0" + record_id + "\0" + section_name + "\0" + chunk).encode("utf-8")
                )
                translated = model.translate_to_arabic(
                    record_id=record_id,
                    section=f"{section_name}:{chunk_index}",
                    text=chunk,
                    source_hash=chunk_hash,
                )
                if not ARABIC_RE.search(translated):
                    raise RuntimeError(f"local translation lacks Arabic for {record_id}/{section_name}")
                missing_numbers = _numbers(chunk) - _numbers(translated)
                if missing_numbers:
                    raise RuntimeError(
                        f"local translation lost numbers for {record_id}/{section_name}: {sorted(missing_numbers)}"
                    )
                pieces.append(translated)
                total_chunks += 1
            translated_fields[output_key] = "\n\n".join(pieces)
            record_units[output_key] = pieces
        translations[record_id] = translated_fields
        translation_units[record_id] = record_units
        print(
            json.dumps(
                {
                    "record": record_index,
                    "total": len(corpus.records),
                    "record_id": record_id,
                    "local_model_calls": model.calls,
                    "cache_hits": model.cache_hits,
                },
                sort_keys=True,
            ),
            flush=True,
        )
    payload: dict[str, object] = {
        "schema_version": TRANSLATION_ASSET_VERSION,
        "source_path": input_path.as_posix(),
        "source_sha256": _sha256(input_path.read_bytes()),
        "model": model.config.model,
        "records": len(translations),
        "chunks": total_chunks,
        "translations": translations,
        "translation_units": translation_units,
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
        handle.write(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
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
                for key in ("records", "chunks", "model", "asset_sha256")
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
