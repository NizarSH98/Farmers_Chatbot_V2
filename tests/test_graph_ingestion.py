from __future__ import annotations

from dataclasses import replace

import pytest

from farmers_chatbot.graph_ingestion import (
    DocumentRecord,
    IngestionBatch,
    IngestionValidationError,
    SemanticSection,
    SourceRecord,
    chunk_semantic_sections,
    content_sha256,
    make_alias,
    make_claim,
    make_entity,
    make_evidence,
    make_project_chunk,
    make_relation,
    make_release_spec,
    normalize_search_text,
    validate_batch,
    validate_project_chunks,
)


def _batch() -> IngestionBatch:
    release = make_release_spec(
        version="draft-2026-08-v1",
        publication_scope="pilot",
        review_policy="draft_allowed",
        embedding_model="provider/multilingual-embedding",
        embedding_dimensions=128,
        source_manifest={"sources": ["MOA-IPM-1"]},
    )
    source = SourceRecord(
        id="source_moa_ipm",
        source_key="MOA-IPM-1",
        title="Integrated pest management guidance",
        publisher="Ministry of Agriculture",
        source_kind="official_public_source",
        evidence_class="A",
        url="https://agriculture.gov.lb/example",
    )
    body = (
        "Inspect leaves twice each week before choosing an intervention. "
        "Record affected plants and ask an extension specialist when symptoms "
        "cannot be distinguished safely."
    )
    document = DocumentRecord(
        id="document_moa_ipm",
        source_id=source.id,
        title="Field scouting",
        language="en",
        content_hash=content_sha256(body),
        review_status="ai_draft",
        geography=("Lebanon",),
    )
    chunks = chunk_semantic_sections(
        release=release,
        source_id=source.id,
        document_id=document.id,
        document_title=document.title,
        language="en",
        review_status="ai_draft",
        risk="medium",
        sections=(SemanticSection("Scouting", body, "decision"),),
        geography=("Lebanon",),
    )
    crop = make_entity("crop", label_en="Potato", label_ar="بطاطا")
    practice = make_entity("practice", label_en="Field scouting", label_ar="الكشف الحقلي")
    alias = make_alias(crop.id, "بطاطا", "ar", script="arabic")
    claim = make_claim(
        "Inspect leaves twice each week before choosing an intervention.",
        "en",
        "ai_draft",
        geography=("Lebanon",),
    )
    relation = make_relation(
        practice.id,
        "applies_to",
        object_entity_id=crop.id,
        review_status="ai_draft",
        geography=("Lebanon",),
    )
    claim_evidence = make_evidence(
        source_id=source.id,
        chunk_id=chunks[0].id,
        excerpt=claim.claim_text,
        claim_id=claim.id,
        confidence=0.98,
    )
    relation_excerpt = "Inspect leaves twice each week"
    relation_evidence = make_evidence(
        source_id=source.id,
        chunk_id=chunks[0].id,
        excerpt=relation_excerpt,
        relation_id=relation.id,
        quote_start=0,
        quote_end=len(relation_excerpt),
    )
    return IngestionBatch(
        release=release,
        sources=(source,),
        documents=(document,),
        chunks=chunks,
        entities=(crop, practice),
        aliases=(alias,),
        claims=(claim,),
        relations=(relation,),
        evidence=(claim_evidence, relation_evidence),
    )


def test_deterministic_bilingual_ingestion_batch() -> None:
    first = _batch()
    second = _batch()
    validate_batch(first)
    assert first == second
    assert first.fingerprint() == second.fingerprint()
    assert first.release.id.startswith("release_")
    assert first.chunks[0].id.startswith("chunk_")
    assert normalize_search_text("آفاتُ البَطاطا ٢٠٢٦") == "افات البطاطا 2026"


def test_heading_chunking_preserves_atomic_decision_blocks() -> None:
    batch = _batch()
    decision = "\n".join(f"Step {index}: observe and record." for index in range(500))
    chunks = chunk_semantic_sections(
        release=batch.release,
        source_id=batch.sources[0].id,
        document_id="large-decision-document",
        document_title="Decision path",
        language="en",
        review_status="ai_draft",
        risk="high",
        sections=(SemanticSection("Do not split", decision, "decision"),),
    )
    assert len(chunks) == 1
    assert chunks[0].content == decision
    assert chunks[0].metadata["atomic_block"] is True


def test_prose_chunking_is_bounded_and_idempotent() -> None:
    batch = _batch()
    prose = " ".join(f"word{index}" for index in range(900))
    values = {
        "release": batch.release,
        "source_id": batch.sources[0].id,
        "document_id": "long-prose-document",
        "document_title": "Long prose",
        "language": "en",
        "review_status": "ai_draft",
        "risk": "low",
        "sections": (SemanticSection("Section", prose),),
    }
    first = chunk_semantic_sections(**values)
    second = chunk_semantic_sections(**values)
    assert first == second
    assert len(first) == 2
    assert all(chunk.token_count <= 450 for chunk in first)


def test_rejects_claim_or_relation_without_passage_evidence() -> None:
    batch = _batch()
    with pytest.raises(IngestionValidationError, match="every relation"):
        validate_batch(replace(batch, evidence=(batch.evidence[0],)))


def test_rejects_excerpt_not_present_in_source_chunk() -> None:
    batch = _batch()
    invalid = replace(batch.evidence[0], excerpt="This sentence is invented.")
    with pytest.raises(IngestionValidationError, match="not present"):
        validate_batch(replace(batch, evidence=(invalid, batch.evidence[1])))


def test_rejects_embedding_model_or_dimension_mixing() -> None:
    batch = _batch()
    invalid_chunk = replace(
        batch.chunks[0],
        embedding_model="different/model",
        embedding=tuple(0.1 for _ in range(128)),
    )
    with pytest.raises(IngestionValidationError, match="embedding configuration"):
        validate_batch(replace(batch, chunks=(invalid_chunk,)))


def test_approved_only_release_rejects_draft_records() -> None:
    batch = _batch()
    approved_release = make_release_spec(
        version="approved-2026-08-v1",
        publication_scope="production",
        review_policy="approved_only",
        embedding_model=batch.release.embedding_model,
        embedding_dimensions=batch.release.embedding_dimensions,
        source_manifest={"sources": ["MOA-IPM-1"]},
    )
    with pytest.raises(IngestionValidationError, match="approved-only"):
        validate_batch(replace(batch, release=approved_release))


def test_live_values_cannot_enter_permanent_release_graph() -> None:
    batch = _batch()
    live_claim = replace(batch.claims[0], dynamicity="live_only")
    with pytest.raises(IngestionValidationError, match="live-only"):
        validate_batch(replace(batch, claims=(live_claim,)))


def test_project_chunks_are_deterministic_and_tenant_scoped() -> None:
    first = make_project_chunk(
        owner_user_id="user-a",
        project_id="project-a",
        document_id="document-a",
        chunk_index=0,
        content="Private field observation",
    )
    second = make_project_chunk(
        owner_user_id="user-b",
        project_id="project-b",
        document_id="document-b",
        chunk_index=0,
        content="Private field observation",
    )
    validate_project_chunks((first, second))
    assert first.id != second.id
    with pytest.raises(IngestionValidationError, match="scope is incomplete"):
        validate_project_chunks((replace(first, owner_user_id=""),))
