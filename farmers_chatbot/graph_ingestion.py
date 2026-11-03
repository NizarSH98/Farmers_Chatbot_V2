"""Deterministic, side-effect-free primitives for versioned GraphRAG ingestion."""

from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

ENTITY_TYPES = frozenset(
    {
        "crop",
        "variety",
        "animal",
        "production_stage",
        "symptom",
        "pest",
        "disease",
        "practice",
        "input",
        "nutrient",
        "soil",
        "water",
        "climate",
        "season",
        "location",
        "farm_system",
        "equipment",
        "measurement",
        "unit",
        "product",
        "value_chain_actor",
        "financial_instrument",
        "organization",
        "service",
        "market",
        "regulation",
        "opportunity",
        "certification",
        "risk",
        "cost",
        "sustainability_impact",
        "outcome",
    }
)

RELATION_TYPES = frozenset(
    {
        "applies_to",
        "requires_context",
        "depends_on",
        "has_stage",
        "has_symptom",
        "located_in",
        "may_cause",
        "may_be_confused_with",
        "supports_action",
        "measured_by",
        "has_unit",
        "targets",
        "affects",
        "controls",
        "prohibits",
        "escalates_to",
        "prevents",
        "requires_live_source",
        "supported_by",
        "increases",
        "decreases",
        "produces",
        "sold_to",
        "provided_by",
        "costs",
        "benefits",
        "alternative_to",
        "compatible_with",
        "contraindicated_with",
        "supersedes",
        "conflicts_with",
        "valid_during",
        "related_to",
    }
)

_ARABIC_DIACRITICS = re.compile(r"[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed]")
_TOKEN = re.compile(r"\w+|[^\w\s]", re.UNICODE)
_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?؟؛])\s+")
_WHITESPACE = re.compile(r"\s+")
_ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")


class IngestionValidationError(ValueError):
    """Raised before any database writes when a graph batch is inconsistent."""


def normalize_search_text(value: str) -> str:
    """Normalize bilingual lookup text without changing stored source wording."""

    normalized = unicodedata.normalize("NFKC", value).casefold().translate(
        _ARABIC_DIGITS
    )
    normalized = _ARABIC_DIACRITICS.sub("", normalized).replace("ـ", "")
    normalized = normalized.translate(
        str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي"})
    )
    return _WHITESPACE.sub(" ", normalized).strip()


def content_sha256(value: str | bytes) -> str:
    encoded = value if isinstance(value, bytes) else value.encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def canonical_json_sha256(value: Any) -> str:
    serialized = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return content_sha256(serialized)


def stable_id(prefix: str, *parts: Any) -> str:
    digest = canonical_json_sha256(parts)[:24]
    return f"{prefix}_{digest}"


@dataclass(frozen=True)
class ReleaseSpec:
    id: str
    version: str
    publication_scope: Literal["internal", "pilot", "production"]
    review_policy: Literal["draft_allowed", "approved_only"]
    embedding_model: str
    embedding_dimensions: int
    source_manifest_sha256: str
    metadata: dict[str, Any] = field(default_factory=dict)
    created_by: str | None = None


def make_release_spec(
    *,
    version: str,
    publication_scope: Literal["internal", "pilot", "production"],
    review_policy: Literal["draft_allowed", "approved_only"],
    embedding_model: str,
    embedding_dimensions: int,
    source_manifest: Any,
    metadata: dict[str, Any] | None = None,
    created_by: str | None = None,
) -> ReleaseSpec:
    manifest_hash = canonical_json_sha256(source_manifest)
    release_id = stable_id(
        "release",
        version,
        publication_scope,
        review_policy,
        embedding_model,
        embedding_dimensions,
        manifest_hash,
    )
    return ReleaseSpec(
        id=release_id,
        version=version.strip(),
        publication_scope=publication_scope,
        review_policy=review_policy,
        embedding_model=embedding_model.strip(),
        embedding_dimensions=embedding_dimensions,
        source_manifest_sha256=manifest_hash,
        metadata=metadata or {},
        created_by=created_by,
    )


@dataclass(frozen=True)
class SourceRecord:
    id: str
    source_key: str
    title: str
    publisher: str
    source_kind: str
    evidence_class: str
    url: str | None = None
    license: str | None = None
    observed_at: str | None = None
    effective_from: str | None = None
    expires_at: str | None = None
    content_hash: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DocumentRecord:
    id: str
    source_id: str
    title: str
    language: str
    content_hash: str
    review_status: str
    translation_status: str = "source"
    retrieval_enabled: bool = True
    geography: tuple[str, ...] = ()
    effective_from: str | None = None
    expires_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ChunkRecord:
    id: str
    document_id: str
    source_id: str
    chunk_index: int
    section_path: str
    language: str
    content: str
    normalized_content: str
    contextualized_content: str
    content_hash: str
    token_count: int
    review_status: str
    risk: str
    embedding_model: str
    embedding_dimensions: int
    embedding: tuple[float, ...] | None = None
    geography: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EntityRecord:
    id: str
    entity_type: str
    canonical_key: str
    label_en: str | None = None
    label_ar: str | None = None
    description: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AliasRecord:
    entity_id: str
    language: str
    alias: str
    normalized_alias: str
    script: str = "unknown"


@dataclass(frozen=True)
class ClaimRecord:
    id: str
    claim_text: str
    language: str
    content_hash: str
    review_status: str
    polarity: str = "positive"
    conditions: dict[str, Any] = field(default_factory=dict)
    geography: tuple[str, ...] = ()
    risk: str = "medium"
    dynamicity: str = "stable"
    effective_from: str | None = None
    expires_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RelationRecord:
    id: str
    subject_entity_id: str
    predicate: str
    object_entity_id: str | None = None
    object_text: str | None = None
    polarity: str = "positive"
    qualifiers: dict[str, Any] = field(default_factory=dict)
    geography: tuple[str, ...] = ()
    risk: str = "medium"
    review_status: str = "ai_draft"
    effective_from: str | None = None
    expires_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EvidenceRecord:
    id: str
    source_id: str
    chunk_id: str
    excerpt: str
    claim_id: str | None = None
    relation_id: str | None = None
    support_type: str = "supports"
    quote_start: int | None = None
    quote_end: int | None = None
    confidence: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class IngestionBatch:
    release: ReleaseSpec
    sources: tuple[SourceRecord, ...]
    documents: tuple[DocumentRecord, ...]
    chunks: tuple[ChunkRecord, ...]
    entities: tuple[EntityRecord, ...] = ()
    aliases: tuple[AliasRecord, ...] = ()
    claims: tuple[ClaimRecord, ...] = ()
    relations: tuple[RelationRecord, ...] = ()
    evidence: tuple[EvidenceRecord, ...] = ()

    def fingerprint(self) -> str:
        return canonical_json_sha256(asdict(self))


@dataclass(frozen=True)
class SemanticSection:
    heading: str
    body: str
    kind: Literal["prose", "table", "decision", "checklist"] = "prose"


@dataclass(frozen=True)
class ProjectChunkRecord:
    id: str
    owner_user_id: str
    project_id: str
    document_id: str
    chunk_index: int
    content: str
    normalized_content: str
    contextualized_content: str
    content_hash: str
    language: str | None = None
    embedding_model: str | None = None
    embedding_dimensions: int | None = None
    embedding: tuple[float, ...] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


def _token_count(value: str) -> int:
    return len(_TOKEN.findall(value))


def _split_large_block(block: str, maximum_tokens: int) -> list[str]:
    sentences = [part.strip() for part in _SENTENCE_BOUNDARY.split(block) if part.strip()]
    if len(sentences) <= 1:
        words = block.split()
        return [
            " ".join(words[start : start + maximum_tokens])
            for start in range(0, len(words), maximum_tokens)
        ]
    pieces: list[str] = []
    current: list[str] = []
    current_tokens = 0
    for sentence in sentences:
        sentence_tokens = _token_count(sentence)
        if current and current_tokens + sentence_tokens > maximum_tokens:
            pieces.append(" ".join(current))
            current = []
            current_tokens = 0
        if sentence_tokens > maximum_tokens:
            pieces.extend(_split_large_block(sentence, maximum_tokens))
        else:
            current.append(sentence)
            current_tokens += sentence_tokens
    if current:
        pieces.append(" ".join(current))
    return pieces


def chunk_semantic_sections(
    *,
    release: ReleaseSpec,
    source_id: str,
    document_id: str,
    document_title: str,
    language: str,
    review_status: str,
    risk: str,
    sections: tuple[SemanticSection, ...],
    geography: tuple[str, ...] = (),
    minimum_tokens: int = 250,
    target_tokens: int = 350,
    maximum_tokens: int = 450,
) -> tuple[ChunkRecord, ...]:
    """Create stable heading-aware chunks while retaining atomic decision blocks."""

    if not 1 <= minimum_tokens <= target_tokens <= maximum_tokens:
        raise IngestionValidationError("invalid semantic chunk size bounds")
    chunks: list[ChunkRecord] = []
    chunk_index = 0
    for section_index, section in enumerate(sections):
        body = section.body.strip()
        if not body:
            continue
        atomic = section.kind in {"table", "decision", "checklist"}
        raw_blocks = [body] if atomic else [
            part.strip() for part in re.split(r"\n\s*\n", body) if part.strip()
        ]
        blocks: list[str] = []
        for block in raw_blocks:
            if not atomic and _token_count(block) > maximum_tokens:
                blocks.extend(_split_large_block(block, maximum_tokens))
            else:
                blocks.append(block)

        packed: list[str] = []
        packed_tokens = 0
        section_chunks: list[str] = []
        for block in blocks:
            block_tokens = _token_count(block)
            if packed and packed_tokens + block_tokens > maximum_tokens:
                section_chunks.append("\n\n".join(packed))
                packed = []
                packed_tokens = 0
            packed.append(block)
            packed_tokens += block_tokens
            if packed_tokens >= target_tokens:
                section_chunks.append("\n\n".join(packed))
                packed = []
                packed_tokens = 0
        if packed:
            tail = "\n\n".join(packed)
            if section_chunks and _token_count(tail) < minimum_tokens and not atomic:
                combined = f"{section_chunks[-1]}\n\n{tail}"
                if _token_count(combined) <= maximum_tokens:
                    section_chunks[-1] = combined
                else:
                    section_chunks.append(tail)
            else:
                section_chunks.append(tail)

        for section_chunk_index, content in enumerate(section_chunks):
            normalized = normalize_search_text(content)
            context = " — ".join(
                part for part in (document_title.strip(), section.heading.strip()) if part
            )
            contextualized = f"{context}\n\n{content}" if context else content
            digest = content_sha256(content)
            identifier = stable_id(
                "chunk", document_id, section_index, section_chunk_index, digest
            )
            chunks.append(
                ChunkRecord(
                    id=identifier,
                    document_id=document_id,
                    source_id=source_id,
                    chunk_index=chunk_index,
                    section_path=section.heading.strip(),
                    language=language,
                    content=content,
                    normalized_content=normalized,
                    contextualized_content=contextualized,
                    content_hash=digest,
                    token_count=max(1, _token_count(content)),
                    review_status=review_status,
                    risk=risk,
                    embedding_model=release.embedding_model,
                    embedding_dimensions=release.embedding_dimensions,
                    geography=geography,
                    metadata={
                        "section_kind": section.kind,
                        "atomic_block": atomic,
                    },
                )
            )
            chunk_index += 1
    return tuple(chunks)


def make_entity(
    entity_type: str,
    *,
    label_en: str | None = None,
    label_ar: str | None = None,
    description: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> EntityRecord:
    if entity_type not in ENTITY_TYPES:
        raise IngestionValidationError(f"unsupported entity type: {entity_type}")
    canonical_key = normalize_search_text(label_en or label_ar or "")
    if not canonical_key:
        raise IngestionValidationError("entity requires an English or Arabic label")
    return EntityRecord(
        id=stable_id("entity", entity_type, canonical_key),
        entity_type=entity_type,
        canonical_key=canonical_key,
        label_en=label_en,
        label_ar=label_ar,
        description=description,
        metadata=metadata or {},
    )


def make_alias(
    entity_id: str,
    alias: str,
    language: str,
    *,
    script: str = "unknown",
) -> AliasRecord:
    normalized = normalize_search_text(alias)
    if not normalized:
        raise IngestionValidationError("entity alias cannot be empty")
    return AliasRecord(entity_id, language, alias.strip(), normalized, script)


def make_claim(
    claim_text: str,
    language: str,
    review_status: str,
    **values: Any,
) -> ClaimRecord:
    cleaned = claim_text.strip()
    if not cleaned:
        raise IngestionValidationError("claim text cannot be empty")
    digest = content_sha256(cleaned)
    return ClaimRecord(
        id=stable_id("claim", language, digest),
        claim_text=cleaned,
        language=language,
        content_hash=digest,
        review_status=review_status,
        **values,
    )


def make_relation(
    subject_entity_id: str,
    predicate: str,
    *,
    object_entity_id: str | None = None,
    object_text: str | None = None,
    **values: Any,
) -> RelationRecord:
    if predicate not in RELATION_TYPES:
        raise IngestionValidationError(f"unsupported relation type: {predicate}")
    if (object_entity_id is None) == (object_text is None):
        raise IngestionValidationError(
            "relation requires exactly one entity or literal object"
        )
    normalized_object = object_entity_id or normalize_search_text(object_text or "")
    identifier = stable_id(
        "relation",
        subject_entity_id,
        predicate,
        normalized_object,
        values.get("qualifiers", {}),
    )
    return RelationRecord(
        id=identifier,
        subject_entity_id=subject_entity_id,
        predicate=predicate,
        object_entity_id=object_entity_id,
        object_text=object_text,
        **values,
    )


def make_evidence(
    *,
    source_id: str,
    chunk_id: str,
    excerpt: str,
    claim_id: str | None = None,
    relation_id: str | None = None,
    **values: Any,
) -> EvidenceRecord:
    if (claim_id is None) == (relation_id is None):
        raise IngestionValidationError(
            "evidence requires exactly one claim or relation target"
        )
    cleaned = excerpt.strip()
    if not cleaned:
        raise IngestionValidationError("evidence excerpt cannot be empty")
    identifier = stable_id(
        "evidence", source_id, chunk_id, claim_id, relation_id, cleaned
    )
    return EvidenceRecord(
        id=identifier,
        source_id=source_id,
        chunk_id=chunk_id,
        excerpt=cleaned,
        claim_id=claim_id,
        relation_id=relation_id,
        **values,
    )


def make_project_chunk(
    *,
    owner_user_id: str,
    project_id: str,
    document_id: str,
    chunk_index: int,
    content: str,
    context: str = "",
    language: str | None = None,
    embedding_model: str | None = None,
    embedding_dimensions: int | None = None,
    embedding: tuple[float, ...] | None = None,
    metadata: dict[str, Any] | None = None,
) -> ProjectChunkRecord:
    cleaned = content.strip()
    if not cleaned:
        raise IngestionValidationError("project chunk content cannot be empty")
    digest = content_sha256(cleaned)
    identifier = stable_id("project_chunk", document_id, chunk_index, digest)
    contextualized = f"{context.strip()}\n\n{cleaned}" if context.strip() else cleaned
    record = ProjectChunkRecord(
        id=identifier,
        owner_user_id=owner_user_id,
        project_id=project_id,
        document_id=document_id,
        chunk_index=chunk_index,
        content=cleaned,
        normalized_content=normalize_search_text(cleaned),
        contextualized_content=contextualized,
        content_hash=digest,
        language=language,
        embedding_model=embedding_model,
        embedding_dimensions=embedding_dimensions,
        embedding=embedding,
        metadata=metadata or {},
    )
    validate_project_chunks((record,))
    return record


def validate_project_chunks(records: tuple[ProjectChunkRecord, ...]) -> None:
    """Validate private chunks without creating graph entities or relations."""

    seen: set[tuple[str, str]] = set()
    for record in records:
        if not record.owner_user_id or not record.project_id or not record.document_id:
            raise IngestionValidationError("project chunk scope is incomplete")
        key = (record.owner_user_id, record.id)
        if key in seen:
            raise IngestionValidationError("duplicate project chunk identifiers")
        seen.add(key)
        if record.content_hash != content_sha256(record.content):
            raise IngestionValidationError("project chunk content hash is invalid")
        if record.id != stable_id(
            "project_chunk", record.document_id, record.chunk_index, record.content_hash
        ):
            raise IngestionValidationError("project chunk identifier is not deterministic")
        configured = record.embedding_model is not None
        if configured != (record.embedding_dimensions is not None):
            raise IngestionValidationError("project embedding configuration is incomplete")
        if record.embedding is not None:
            if record.embedding_dimensions is None or (
                len(record.embedding) != record.embedding_dimensions
            ):
                raise IngestionValidationError("project embedding dimensions differ")
            if not all(math.isfinite(value) for value in record.embedding):
                raise IngestionValidationError("project embedding contains non-finite values")


def _require_unique(label: str, values: list[str]) -> None:
    if len(values) != len(set(values)):
        raise IngestionValidationError(f"duplicate {label} identifiers")


def validate_batch(batch: IngestionBatch) -> None:
    """Validate references, provenance, embeddings, and graph evidence."""

    release = batch.release
    if not release.version or not release.embedding_model:
        raise IngestionValidationError("release version and embedding model are required")
    if not 128 <= release.embedding_dimensions <= 4096:
        raise IngestionValidationError("embedding dimensions must be between 128 and 4096")
    if len(release.source_manifest_sha256) != 64:
        raise IngestionValidationError("release source manifest hash is invalid")
    if not batch.sources or not batch.documents or not batch.chunks:
        raise IngestionValidationError(
            "a release requires at least one source, document, and chunk"
        )

    source_ids = [record.id for record in batch.sources]
    document_ids = [record.id for record in batch.documents]
    chunk_ids = [record.id for record in batch.chunks]
    entity_ids = [record.id for record in batch.entities]
    claim_ids = [record.id for record in batch.claims]
    relation_ids = [record.id for record in batch.relations]
    evidence_ids = [record.id for record in batch.evidence]
    for label, values in (
        ("source", source_ids),
        ("document", document_ids),
        ("chunk", chunk_ids),
        ("entity", entity_ids),
        ("claim", claim_ids),
        ("relation", relation_ids),
        ("evidence", evidence_ids),
    ):
        _require_unique(label, values)

    source_set = set(source_ids)
    documents = {record.id: record for record in batch.documents}
    chunks = {record.id: record for record in batch.chunks}
    entity_set = set(entity_ids)
    claim_set = set(claim_ids)
    relation_set = set(relation_ids)

    for document in batch.documents:
        if document.source_id not in source_set:
            raise IngestionValidationError("document references an unknown source")
    for chunk in batch.chunks:
        document = documents.get(chunk.document_id)
        if document is None or document.source_id != chunk.source_id:
            raise IngestionValidationError("chunk provenance does not match its document")
        if chunk.content_hash != content_sha256(chunk.content):
            raise IngestionValidationError("chunk content hash does not match its text")
        if (
            chunk.embedding_model != release.embedding_model
            or chunk.embedding_dimensions != release.embedding_dimensions
        ):
            raise IngestionValidationError(
                "chunk embedding configuration differs from its release"
            )
        if chunk.embedding is not None and (
            len(chunk.embedding) != release.embedding_dimensions
            or not all(math.isfinite(value) for value in chunk.embedding)
        ):
            raise IngestionValidationError("chunk embedding is invalid")
    for entity in batch.entities:
        if entity.entity_type not in ENTITY_TYPES:
            raise IngestionValidationError("entity has an unsupported type")
        if entity.id != stable_id("entity", entity.entity_type, entity.canonical_key):
            raise IngestionValidationError("entity identifier is not deterministic")
    for alias in batch.aliases:
        if alias.entity_id not in entity_set:
            raise IngestionValidationError("alias references an unknown entity")
        if alias.normalized_alias != normalize_search_text(alias.alias):
            raise IngestionValidationError("alias normalization is inconsistent")
    for claim in batch.claims:
        if claim.content_hash != content_sha256(claim.claim_text):
            raise IngestionValidationError("claim content hash does not match its text")
        if claim.dynamicity == "live_only":
            raise IngestionValidationError(
                "live-only values belong in timestamped live evidence, not a release"
            )
    for relation in batch.relations:
        if relation.predicate not in RELATION_TYPES:
            raise IngestionValidationError("relation has an unsupported predicate")
        if relation.subject_entity_id not in entity_set:
            raise IngestionValidationError("relation subject is unknown")
        if (relation.object_entity_id is None) == (relation.object_text is None):
            raise IngestionValidationError("relation object is ambiguous")
        if (
            relation.object_entity_id is not None
            and relation.object_entity_id not in entity_set
        ):
            raise IngestionValidationError("relation object is unknown")

    claims_with_evidence: set[str] = set()
    relations_with_evidence: set[str] = set()
    for evidence in batch.evidence:
        chunk = chunks.get(evidence.chunk_id)
        if chunk is None or chunk.source_id != evidence.source_id:
            raise IngestionValidationError("evidence provenance is inconsistent")
        if normalize_search_text(evidence.excerpt) not in normalize_search_text(
            chunk.content
        ):
            raise IngestionValidationError("evidence excerpt is not present in its chunk")
        if evidence.confidence is not None and not 0 <= evidence.confidence <= 1:
            raise IngestionValidationError("evidence confidence must be between zero and one")
        if (
            evidence.quote_start is not None or evidence.quote_end is not None
        ) and (
                evidence.quote_start is None
                or evidence.quote_end is None
                or evidence.quote_start < 0
                or evidence.quote_end <= evidence.quote_start
                or chunk.content[evidence.quote_start : evidence.quote_end]
                != evidence.excerpt
        ):
            raise IngestionValidationError("evidence quote offsets are inconsistent")
        if (evidence.claim_id is None) == (evidence.relation_id is None):
            raise IngestionValidationError("evidence target is ambiguous")
        if evidence.claim_id is not None:
            if evidence.claim_id not in claim_set:
                raise IngestionValidationError("evidence claim target is unknown")
            claims_with_evidence.add(evidence.claim_id)
        if evidence.relation_id is not None:
            if evidence.relation_id not in relation_set:
                raise IngestionValidationError("evidence relation target is unknown")
            relations_with_evidence.add(evidence.relation_id)
    if claim_set - claims_with_evidence:
        raise IngestionValidationError("every claim requires passage evidence")
    if relation_set - relations_with_evidence:
        raise IngestionValidationError("every relation requires passage evidence")
    if release.review_policy == "approved_only":
        review_states = [
            *(document.review_status for document in batch.documents),
            *(chunk.review_status for chunk in batch.chunks),
            *(claim.review_status for claim in batch.claims),
            *(relation.review_status for relation in batch.relations),
        ]
        if any(status != "approved" for status in review_states):
            raise IngestionValidationError(
                "approved-only releases cannot contain unapproved retrievable records"
            )
