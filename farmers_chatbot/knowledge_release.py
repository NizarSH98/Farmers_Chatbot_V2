"""Build a deterministic GraphRAG ingestion batch from canonical Markdown."""

from __future__ import annotations

import hashlib
from pathlib import Path

from .agrifood_ontology import (
    ENTITIES,
    ONTOLOGY_VERSION,
    RELATIONS,
    ontology_fingerprint,
    validate_ontology,
)
from .graph_ingestion import (
    AliasRecord,
    ChunkRecord,
    DocumentRecord,
    EntityRecord,
    IngestionBatch,
    SemanticSection,
    SourceRecord,
    chunk_semantic_sections,
    content_sha256,
    make_alias,
    make_claim,
    make_entity,
    make_evidence,
    make_relation,
    make_release_spec,
    stable_id,
    validate_batch,
)
from .knowledge_markdown import MarkdownRecord, parse_knowledge_markdown

PARSER_VERSION = "raise-markdown-v0.2-parser-2"
COMPILED_SOURCE_ID = "RAISE-AGRIFOOD-DRAFT-V0.2"


def _source(item: dict[str, object]) -> SourceRecord:
    return SourceRecord(
        id=str(item["id"]), source_key=str(item["id"]),
        title=str(item.get("title") or item["id"]),
        publisher=str(item.get("publisher") or "unknown publisher"),
        source_kind="official_public_source",
        evidence_class=str(item.get("source_class") or "unclassified"),
        url=str(item["url"]) if item.get("url") else None,
        observed_at=str(item["accessed"]) if item.get("accessed") else None,
        metadata={"legacy_ids": item.get("legacy_ids") or [], "retrieval_enabled": False},
    )


def _sections(record: MarkdownRecord, language: str) -> tuple[SemanticSection, ...]:
    if language == "en":
        values = (
            ("English guidance", "prose"), ("Decision logic", "decision"),
            ("Safe next action", "checklist"), ("Avoid or escalate", "decision"),
            ("Evidence and applicability limits", "prose"),
        )
    else:
        values = (
            ("Arabic guidance — machine draft", "prose"),
            ("منطق القرار — مسودة آلية", "decision"),
            ("الخطوة التالية الآمنة — مسودة آلية", "checklist"),
            ("ما يجب تجنبه أو تصعيده — مسودة آلية", "decision"),
            ("حدود الأدلة وقابلية التطبيق — مسودة آلية", "prose"),
        )
    return tuple(
        SemanticSection(heading=heading, body=record.sections[heading], kind=kind)  # type: ignore[arg-type]
        for heading, kind in values
    )


def build_release_batch(
    path: str | Path,
    *,
    embedding_model: str = "lexical-only",
    embedding_dimensions: int = 768,
    embedding_approval: dict[str, object] | None = None,
    created_by: str | None = None,
) -> IngestionBatch:
    source_path = Path(path)
    corpus = parse_knowledge_markdown(source_path)
    record_ids = {str(record.metadata["id"]) for record in corpus.records}
    validate_ontology(record_ids)
    manifest = {
        "markdown_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "source_doc_sha256": corpus.front_matter["source_doc_sha256"],
        "source_ids": sorted(corpus.sources),
        "parser_version": PARSER_VERSION,
        "ontology_version": ONTOLOGY_VERSION,
        "ontology_sha256": ontology_fingerprint(),
        "embedding_approval": embedding_approval,
    }
    release = make_release_spec(
        version=str(corpus.front_matter["version"]), publication_scope="pilot",
        review_policy="draft_allowed", embedding_model=embedding_model,
        embedding_dimensions=embedding_dimensions, source_manifest=manifest,
        metadata={
            "document_id": corpus.front_matter["document_id"],
            "production_eligible": False,
            "embedding_approval": embedding_approval,
        },
        created_by=created_by,
    )
    sources = [_source(item) for item in corpus.sources.values()]
    sources.append(SourceRecord(
        id=COMPILED_SOURCE_ID, source_key=COMPILED_SOURCE_ID,
        title="RAISE Agrifood Knowledge Draft v0.2", publisher="RAISE project",
        source_kind="compiled_ai_draft", evidence_class="draft_synthesis",
        content_hash=manifest["markdown_sha256"],
        metadata={"production_eligible": False, "source_ids": sorted(corpus.sources)},
    ))
    entities: list[EntityRecord] = []
    aliases: list[AliasRecord] = []
    entity_by_key: dict[str, EntityRecord] = {}
    for specification in ENTITIES:
        entity = make_entity(
            specification.entity_type,
            label_en=specification.label_en,
            label_ar=specification.label_ar,
            metadata={
                "ontology_key": specification.key,
                "ontology_version": ONTOLOGY_VERSION,
                "record_ids": list(specification.record_ids),
            },
        )
        entities.append(entity)
        entity_by_key[specification.key] = entity
        aliases.extend(
            (
                make_alias(entity.id, specification.label_en, "en", script="latin"),
                make_alias(entity.id, specification.label_ar, "ar", script="arabic"),
            )
        )
        aliases.extend(
            make_alias(
                entity.id,
                alias.text,
                alias.language,
                script=alias.script,
            )
            for alias in specification.aliases
        )

    documents, chunks, claims, relations, evidence = [], [], [], [], []
    chunks_by_record_language: dict[tuple[str, str], tuple[ChunkRecord, ...]] = {}
    for record in corpus.records:
        record_id = str(record.metadata["id"])
        for language in ("en", "ar"):
            sections = _sections(record, language)
            joined = "\n\n".join(section.body for section in sections)
            document_id = stable_id("document", record_id, language, content_sha256(joined))
            documents.append(DocumentRecord(
                id=document_id, source_id=COMPILED_SOURCE_ID,
                title=str(record.metadata[f"title_{language}"]), language=language,
                content_hash=content_sha256(joined), review_status="ai_draft",
                translation_status="source" if language == "en" else "machine_draft",
                retrieval_enabled=True,
                geography=tuple(str(item) for item in record.metadata["geography"]),
                metadata={"record_id": record_id, "source_ids": record.metadata["source_ids"]},
            ))
            made = chunk_semantic_sections(
                release=release, source_id=COMPILED_SOURCE_ID, document_id=document_id,
                document_title=str(record.metadata[f"title_{language}"]), language=language,
                review_status="ai_draft", risk=str(record.metadata["risk"]),
                sections=sections,
                geography=tuple(str(item) for item in record.metadata["geography"]),
            )
            chunks.extend(made)
            chunks_by_record_language[(record_id, language)] = made
            for chunk in made:
                claim = make_claim(
                    chunk.content, language, "ai_draft", risk=str(record.metadata["risk"]),
                    dynamicity="stable", geography=tuple(str(item) for item in record.metadata["geography"]),
                    metadata={"record_id": record_id, "declared_dynamicity": record.metadata["dynamicity"]},
                )
                claims.append(claim)
                evidence.append(make_evidence(
                    source_id=COMPILED_SOURCE_ID, chunk_id=chunk.id,
                    excerpt=chunk.content, claim_id=claim.id, confidence=1.0,
                    metadata={"source_ids": record.metadata["source_ids"]},
                ))

    records_by_id = {
        str(record.metadata["id"]): record for record in corpus.records
    }
    for specification in RELATIONS:
        record = records_by_id[specification.record_id]
        support_chunks = [
            chunk
            for chunk in chunks_by_record_language[(specification.record_id, "en")]
            if chunk.section_path == specification.evidence_section
        ]
        if not support_chunks:
            raise ValueError(
                "Ontology relation evidence section has no compiled chunk: "
                f"{specification.record_id}/{specification.evidence_section}"
            )
        support_chunk = support_chunks[0]
        qualifiers = {
            "ontology_version": ONTOLOGY_VERSION,
            "record_id": specification.record_id,
            **specification.qualifiers,
        }
        relation = make_relation(
            entity_by_key[specification.subject].id,
            specification.predicate,
            object_entity_id=entity_by_key[specification.object].id,
            polarity=specification.polarity,
            qualifiers=qualifiers,
            risk=specification.risk,
            review_status="ai_draft",
            geography=tuple(str(item) for item in record.metadata["geography"]),
            metadata={
                "record_id": specification.record_id,
                "source_ids": record.metadata["source_ids"],
                "subject_key": specification.subject,
                "object_key": specification.object,
                "evidence_section": specification.evidence_section,
            },
        )
        relations.append(relation)
        evidence.append(
            make_evidence(
                source_id=COMPILED_SOURCE_ID,
                chunk_id=support_chunk.id,
                excerpt=support_chunk.content,
                relation_id=relation.id,
                confidence=0.75,
                metadata={
                    "source_ids": record.metadata["source_ids"],
                    "curation_status": "ai_draft",
                    "ontology_version": ONTOLOGY_VERSION,
                },
            )
        )
    batch = IngestionBatch(
        release=release, sources=tuple(sources), documents=tuple(documents),
        chunks=tuple(chunks), entities=tuple(entities), aliases=tuple(aliases),
        claims=tuple(claims), relations=tuple(relations), evidence=tuple(evidence),
    )
    validate_batch(batch)
    return batch
