from __future__ import annotations

import hashlib
import json
import socket
from argparse import Namespace
from pathlib import Path

from farmers_chatbot.agrifood_ontology import ENTITIES, RELATIONS
from farmers_chatbot.knowledge_markdown import parse_knowledge_markdown
from farmers_chatbot.knowledge_release import build_release_batch
from scripts.agrifood_arabic_drafts import (
    ARABIC_DRAFTS,
    REQUIRED_ARABIC_FIELDS,
)
from scripts.convert_agrifood_docx import (
    LEGACY_JSON_EXCLUSIONS,
    SOURCE_SHA256,
    SPECS,
    replace_source_ids,
    run,
    source_ids_in_text,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DOCX = (
    ROOT / "knowledge_base" / "ESDU_Agrifood_Knowledge_Base_v0.1.docx"
)


def test_local_arabic_drafts_cover_every_graph_record() -> None:
    assert set(ARABIC_DRAFTS) == {spec.record_id for spec in SPECS}
    assert all(set(fields) == REQUIRED_ARABIC_FIELDS for fields in ARABIC_DRAFTS.values())
    assert all(
        any("\u0600" <= character <= "\u06ff" for character in text)
        for fields in ARABIC_DRAFTS.values()
        for text in fields.values()
    )


def test_opaque_source_ranges_and_lists_are_fully_reconciled() -> None:
    value = "Use [S12–S13], compare [S15, S17], and retain [S01]."
    assert source_ids_in_text(value) == {
        "ESDU-HOME-2026",
        "FAO-WATER-QUALITY-1985",
        "FAO-SOIL-TESTING-2019",
        "CODEX-FOOD-HYGIENE-CXC1-2022",
        "WHO-GROWING-SAFER-PRODUCE-2012",
    }
    reconciled = replace_source_ids(value)
    assert not any(marker in reconciled for marker in ("[S12", "[S15", "[S01]"))


def test_docx_conversion_is_offline_bilingual_and_graph_ready(
    monkeypatch,
    tmp_path: Path,
) -> None:
    before = hashlib.sha256(SOURCE_DOCX.read_bytes()).hexdigest().upper()
    assert before == SOURCE_SHA256

    def block_network(*args, **kwargs):
        raise AssertionError("offline corpus conversion attempted network access")

    monkeypatch.setattr(socket, "create_connection", block_network)
    output = tmp_path / "agrifood_knowledge_draft_v0.2.md"
    arabic_output = tmp_path / "agrifood_knowledge_draft_v0.2_ar.md"
    run(
        Namespace(
            input=SOURCE_DOCX,
            output=output,
            arabic_output=arabic_output,
            guide=ROOT / "knowledge_base" / "guide.json",
            sources=ROOT / "knowledge_base" / "sources.json",
        )
    )

    assert output.exists()
    assert arabic_output.exists()
    assert hashlib.sha256(SOURCE_DOCX.read_bytes()).hexdigest().upper() == before

    corpus = parse_knowledge_markdown(output)
    assert len(corpus.records) == len(SPECS)
    assert len(corpus.sources) == 35
    assert all(
        record.metadata["translation_method"] == "local_opus_mt_with_reviewed_overrides_and_semantic_validation"
        for record in corpus.records
    )
    legacy_ids = {
        str(item["id"])
        for item in json.loads(
            (ROOT / "knowledge_base" / "guide.json").read_text(encoding="utf-8")
        )["items"]
    }
    merged_ids = {
        str(item)
        for record in corpus.records
        for item in record.metadata["supersedes_legacy_items"]
    }
    assert merged_ids.isdisjoint(LEGACY_JSON_EXCLUSIONS)
    assert merged_ids | set(LEGACY_JSON_EXCLUSIONS) == legacy_ids
    batch = build_release_batch(output)
    assert len(batch.documents) == len(SPECS) * 2
    assert len(batch.entities) == len(ENTITIES)
    assert len(batch.relations) == len(RELATIONS)
    assert all(item.review_status == "approved" for item in batch.claims)

    arabic = arabic_output.read_text(encoding="utf-8")
    assert arabic.count("\n## ") == len(SPECS)
    assert "translation_method: local_opus_mt_with_reviewed_overrides_and_semantic_validation" in arabic
    assert "OpenRouter" not in arabic
    assert "\ufffd" not in arabic
    assert all(f'"id": "{spec.record_id}"' in arabic for spec in SPECS)
    assert "# ملحق المصادر والتحقق غير القابل للاسترجاع" in arabic

    canonical_hash = hashlib.sha256(output.read_bytes()).hexdigest()
    arabic_hash = hashlib.sha256(arabic_output.read_bytes()).hexdigest()
    run(
        Namespace(
            input=SOURCE_DOCX,
            output=output,
            arabic_output=arabic_output,
            guide=ROOT / "knowledge_base" / "guide.json",
            sources=ROOT / "knowledge_base" / "sources.json",
        )
    )
    assert hashlib.sha256(output.read_bytes()).hexdigest() == canonical_hash
    assert hashlib.sha256(arabic_output.read_bytes()).hexdigest() == arabic_hash
