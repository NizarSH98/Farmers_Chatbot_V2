"""Transactional PostgreSQL repository for versioned GraphRAG releases."""

from __future__ import annotations

import json
import math
from collections.abc import Callable, Mapping, Sequence
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Any

from .graph_ingestion import (
    IngestionBatch,
    ProjectChunkRecord,
    ReleaseSpec,
    normalize_search_text,
    stable_id,
    validate_batch,
    validate_project_chunks,
)

ConnectionFactory = Callable[[], AbstractContextManager[Any]]


class GraphRepositoryError(RuntimeError):
    """Base error for release and graph persistence failures."""


class GraphConflictError(GraphRepositoryError):
    """Raised when a deterministic identifier is reused with different inputs."""


class GraphIntegrityError(GraphRepositoryError):
    """Raised when a release cannot be sealed or activated safely."""


@dataclass(frozen=True)
class ActivationResult:
    deployment_scope: str
    release_id: str
    previous_release_id: str | None
    rolled_back: bool = False


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _vector(value: Sequence[float] | None) -> str | None:
    if value is None:
        return None
    if not value or not all(math.isfinite(float(item)) for item in value):
        raise GraphIntegrityError("embedding must contain finite numeric values")
    return "[" + ",".join(format(float(item), ".12g") for item in value) + "]"


def _vector_tuple(value: Any) -> tuple[float, ...]:
    if isinstance(value, str):
        stripped = value.strip().removeprefix("[").removesuffix("]")
        values = [] if not stripped else stripped.split(",")
    elif isinstance(value, Sequence):
        values = value
    else:
        raise GraphIntegrityError("cached embedding has an unsupported representation")
    result = tuple(float(item) for item in values)
    if not result or not all(math.isfinite(item) for item in result):
        raise GraphIntegrityError("cached embedding is invalid")
    return result


def _row_value(row: Any, key: str, index: int) -> Any:
    if row is None:
        return None
    if isinstance(row, Mapping):
        return row.get(key)
    return row[index]


class GraphRepository:
    """Persist immutable releases through caller-owned transactional connections."""

    def __init__(self, connection_factory: ConnectionFactory) -> None:
        self._connection_factory = connection_factory

    def create_release(self, spec: ReleaseSpec) -> dict[str, Any]:
        with self._connection_factory() as connection:
            connection.execute(
                """
                INSERT INTO knowledge_releases (
                    id, version, publication_scope, review_policy,
                    embedding_model, embedding_dimensions,
                    source_manifest_sha256, metadata_json, created_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                (
                    spec.id,
                    spec.version,
                    spec.publication_scope,
                    spec.review_policy,
                    spec.embedding_model,
                    spec.embedding_dimensions,
                    spec.source_manifest_sha256,
                    _json(spec.metadata),
                    spec.created_by,
                ),
            )
            row = connection.execute(
                """
                SELECT id, version, publication_scope, review_policy,
                       embedding_model, embedding_dimensions,
                       source_manifest_sha256, state, sealed_at
                FROM knowledge_releases WHERE id = %s
                """,
                (spec.id,),
            ).fetchone()
            if row is None:
                raise GraphRepositoryError("knowledge release could not be created")
            expected = (
                spec.id,
                spec.version,
                spec.publication_scope,
                spec.review_policy,
                spec.embedding_model,
                spec.embedding_dimensions,
                spec.source_manifest_sha256,
            )
            actual = tuple(
                _row_value(row, key, index)
                for index, key in enumerate(
                    (
                        "id",
                        "version",
                        "publication_scope",
                        "review_policy",
                        "embedding_model",
                        "embedding_dimensions",
                        "source_manifest_sha256",
                    )
                )
            )
            if actual != expected:
                raise GraphConflictError(
                    "release identifier already exists with different immutable inputs"
                )
            return dict(row) if isinstance(row, Mapping) else {
                "id": row[0],
                "version": row[1],
                "publication_scope": row[2],
                "review_policy": row[3],
                "embedding_model": row[4],
                "embedding_dimensions": row[5],
                "source_manifest_sha256": row[6],
                "state": row[7],
                "sealed_at": row[8],
            }

    def begin_ingestion(
        self,
        release_id: str,
        input_sha256: str,
        *,
        parser_version: str,
    ) -> dict[str, Any]:
        run_id = stable_id("ingestion", release_id, input_sha256, parser_version)
        with self._connection_factory() as connection:
            connection.execute(
                """
                INSERT INTO graph_ingestion_runs (
                    id, release_id, input_sha256, parser_version
                ) VALUES (%s, %s, %s, %s)
                ON CONFLICT (release_id, input_sha256) DO NOTHING
                """,
                (run_id, release_id, input_sha256, parser_version),
            )
            row = connection.execute(
                """
                SELECT id, release_id, input_sha256, parser_version, state, stats_json
                FROM graph_ingestion_runs
                WHERE release_id = %s AND input_sha256 = %s
                """,
                (release_id, input_sha256),
            ).fetchone()
            if row is None:
                raise GraphRepositoryError("ingestion run could not be reserved")
            existing_parser = _row_value(row, "parser_version", 3)
            if existing_parser != parser_version:
                raise GraphConflictError(
                    "input was already ingested with a different parser version"
                )
            if _row_value(row, "state", 4) == "failed":
                connection.execute(
                    """
                    UPDATE graph_ingestion_runs
                    SET state = 'running', stats_json = '{}'::jsonb,
                        error_type = NULL, completed_at = NULL, started_at = now()
                    WHERE id = %s AND state = 'failed'
                    """,
                    (str(_row_value(row, "id", 0)),),
                )
                if isinstance(row, Mapping):
                    row = {**row, "state": "running", "stats_json": {}}
                else:
                    row = (*row[:4], "running", {})
            return dict(row) if isinstance(row, Mapping) else {
                "id": row[0],
                "release_id": row[1],
                "input_sha256": row[2],
                "parser_version": row[3],
                "state": row[4],
                "stats_json": row[5],
            }

    def ingest_batch(self, batch: IngestionBatch) -> dict[str, int]:
        """Insert a validated batch atomically; stable IDs make retries idempotent."""

        validate_batch(batch)
        release_id = batch.release.id
        with self._connection_factory() as connection:
            state_row = connection.execute(
                "SELECT state FROM knowledge_releases WHERE id = %s FOR UPDATE",
                (release_id,),
            ).fetchone()
            if state_row is None:
                raise GraphRepositoryError("knowledge release does not exist")
            if _row_value(state_row, "state", 0) != "building":
                raise GraphIntegrityError("only a building release can accept ingestion")

            for source in batch.sources:
                connection.execute(
                    """
                    INSERT INTO graph_sources (
                        release_id, id, source_key, title, publisher, source_kind,
                        evidence_class, url, license, observed_at, effective_from,
                        expires_at, content_sha256, metadata_json
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s::timestamptz, %s::timestamptz, %s::timestamptz,
                        %s, %s::jsonb
                    ) ON CONFLICT (release_id, id) DO NOTHING
                    """,
                    (
                        release_id,
                        source.id,
                        source.source_key,
                        source.title,
                        source.publisher,
                        source.source_kind,
                        source.evidence_class,
                        source.url,
                        source.license,
                        source.observed_at,
                        source.effective_from,
                        source.expires_at,
                        source.content_hash,
                        _json(source.metadata),
                    ),
                )
            for document in batch.documents:
                connection.execute(
                    """
                    INSERT INTO graph_documents (
                        release_id, id, source_id, title, language, content_sha256,
                        review_status, translation_status, retrieval_enabled,
                        geography_json, effective_from, expires_at, metadata_json
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb,
                        %s::timestamptz, %s::timestamptz, %s::jsonb
                    ) ON CONFLICT (release_id, id) DO NOTHING
                    """,
                    (
                        release_id,
                        document.id,
                        document.source_id,
                        document.title,
                        document.language,
                        document.content_hash,
                        document.review_status,
                        document.translation_status,
                        document.retrieval_enabled,
                        _json(document.geography),
                        document.effective_from,
                        document.expires_at,
                        _json(document.metadata),
                    ),
                )
            for chunk in batch.chunks:
                connection.execute(
                    """
                    INSERT INTO graph_chunks (
                        release_id, id, document_id, source_id, chunk_index,
                        section_path, language, content, normalized_content,
                        contextualized_content, content_sha256, token_count,
                        review_status, risk, geography_json, embedding_model,
                        embedding_dimensions, embedding, metadata_json
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s::jsonb, %s, %s, %s::vector, %s::jsonb
                    ) ON CONFLICT (release_id, id) DO NOTHING
                    """,
                    (
                        release_id,
                        chunk.id,
                        chunk.document_id,
                        chunk.source_id,
                        chunk.chunk_index,
                        chunk.section_path,
                        chunk.language,
                        chunk.content,
                        chunk.normalized_content,
                        chunk.contextualized_content,
                        chunk.content_hash,
                        chunk.token_count,
                        chunk.review_status,
                        chunk.risk,
                        _json(chunk.geography),
                        chunk.embedding_model,
                        chunk.embedding_dimensions,
                        _vector(chunk.embedding),
                        _json(chunk.metadata),
                    ),
                )
            for entity in batch.entities:
                connection.execute(
                    """
                    INSERT INTO graph_entities (
                        release_id, id, entity_type, canonical_key, label_en,
                        label_ar, description, metadata_json
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                    ON CONFLICT (release_id, id) DO NOTHING
                    """,
                    (
                        release_id,
                        entity.id,
                        entity.entity_type,
                        entity.canonical_key,
                        entity.label_en,
                        entity.label_ar,
                        entity.description,
                        _json(entity.metadata),
                    ),
                )
            for alias in batch.aliases:
                connection.execute(
                    """
                    INSERT INTO graph_entity_aliases (
                        release_id, entity_id, language, script, alias,
                        normalized_alias
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (
                        release_id, entity_id, language, normalized_alias
                    ) DO NOTHING
                    """,
                    (
                        release_id,
                        alias.entity_id,
                        alias.language,
                        alias.script,
                        alias.alias,
                        alias.normalized_alias,
                    ),
                )
            for claim in batch.claims:
                connection.execute(
                    """
                    INSERT INTO graph_claims (
                        release_id, id, claim_text, language, polarity,
                        conditions_json, geography_json, risk, review_status,
                        dynamicity, effective_from, expires_at, content_sha256,
                        metadata_json
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s,
                        %s, %s::timestamptz, %s::timestamptz, %s, %s::jsonb
                    ) ON CONFLICT (release_id, id) DO NOTHING
                    """,
                    (
                        release_id,
                        claim.id,
                        claim.claim_text,
                        claim.language,
                        claim.polarity,
                        _json(claim.conditions),
                        _json(claim.geography),
                        claim.risk,
                        claim.review_status,
                        claim.dynamicity,
                        claim.effective_from,
                        claim.expires_at,
                        claim.content_hash,
                        _json(claim.metadata),
                    ),
                )
            for relation in batch.relations:
                connection.execute(
                    """
                    INSERT INTO graph_relations (
                        release_id, id, subject_entity_id, predicate,
                        object_entity_id, object_text, polarity, qualifiers_json,
                        geography_json, risk, review_status, effective_from,
                        expires_at, metadata_json
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb,
                        %s, %s, %s::timestamptz, %s::timestamptz, %s::jsonb
                    ) ON CONFLICT (release_id, id) DO NOTHING
                    """,
                    (
                        release_id,
                        relation.id,
                        relation.subject_entity_id,
                        relation.predicate,
                        relation.object_entity_id,
                        relation.object_text,
                        relation.polarity,
                        _json(relation.qualifiers),
                        _json(relation.geography),
                        relation.risk,
                        relation.review_status,
                        relation.effective_from,
                        relation.expires_at,
                        _json(relation.metadata),
                    ),
                )
            for evidence in batch.evidence:
                connection.execute(
                    """
                    INSERT INTO graph_evidence_links (
                        release_id, id, source_id, chunk_id, claim_id,
                        relation_id, support_type, excerpt, quote_start,
                        quote_end, confidence, metadata_json
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s::jsonb
                    ) ON CONFLICT (release_id, id) DO NOTHING
                    """,
                    (
                        release_id,
                        evidence.id,
                        evidence.source_id,
                        evidence.chunk_id,
                        evidence.claim_id,
                        evidence.relation_id,
                        evidence.support_type,
                        evidence.excerpt,
                        evidence.quote_start,
                        evidence.quote_end,
                        evidence.confidence,
                        _json(evidence.metadata),
                    ),
                )
        return {
            "sources": len(batch.sources),
            "documents": len(batch.documents),
            "chunks": len(batch.chunks),
            "entities": len(batch.entities),
            "claims": len(batch.claims),
            "relations": len(batch.relations),
            "evidence": len(batch.evidence),
        }

    def complete_ingestion(
        self,
        run_id: str,
        *,
        stats: Mapping[str, Any],
        error_type: str | None = None,
    ) -> None:
        state = "failed" if error_type else "completed"
        with self._connection_factory() as connection:
            cursor = connection.execute(
                """
                UPDATE graph_ingestion_runs
                SET state = %s, stats_json = %s::jsonb, error_type = %s,
                    completed_at = now()
                WHERE id = %s AND state = 'running'
                """,
                (state, _json(dict(stats)), error_type, run_id),
            )
            if cursor.rowcount != 1:
                raise GraphConflictError("ingestion run is not in the running state")

    def seal_release(self, release_id: str) -> dict[str, int]:
        """Validate provenance and freeze a complete release atomically."""

        with self._connection_factory() as connection:
            connection.execute(
                "SELECT pg_advisory_xact_lock(hashtext(%s))",
                (f"knowledge-release:{release_id}",),
            )
            release = connection.execute(
                """
                SELECT state, sealed_at FROM knowledge_releases
                WHERE id = %s FOR UPDATE
                """,
                (release_id,),
            ).fetchone()
            if release is None:
                raise GraphRepositoryError("knowledge release does not exist")
            if _row_value(release, "state", 0) == "ready":
                return self._release_counts(connection, release_id)
            if _row_value(release, "state", 0) != "building":
                raise GraphIntegrityError("failed releases cannot be sealed")
            counts = self._release_counts(connection, release_id)
            if min(counts["sources"], counts["documents"], counts["chunks"]) < 1:
                raise GraphIntegrityError(
                    "release requires at least one source, document, and chunk"
                )
            if counts["running_runs"] or counts["failed_runs"]:
                raise GraphIntegrityError("all ingestion runs must complete successfully")
            if counts["completed_runs"] < 1:
                raise GraphIntegrityError("release has no completed ingestion run")
            if counts["claims_without_evidence"]:
                raise GraphIntegrityError("release contains claims without evidence")
            if counts["relations_without_evidence"]:
                raise GraphIntegrityError("release contains relations without evidence")
            connection.execute(
                """
                UPDATE knowledge_releases
                SET state = 'ready', sealed_at = now()
                WHERE id = %s AND state = 'building'
                """,
                (release_id,),
            )
            return counts

    @staticmethod
    def _release_counts(connection: Any, release_id: str) -> dict[str, int]:
        row = connection.execute(
            """
            SELECT
                (SELECT count(*) FROM graph_sources WHERE release_id = %s) AS sources,
                (SELECT count(*) FROM graph_documents WHERE release_id = %s) AS documents,
                (SELECT count(*) FROM graph_chunks WHERE release_id = %s) AS chunks,
                (SELECT count(*) FROM graph_ingestion_runs
                    WHERE release_id = %s AND state = 'running') AS running_runs,
                (SELECT count(*) FROM graph_ingestion_runs
                    WHERE release_id = %s AND state = 'failed') AS failed_runs,
                (SELECT count(*) FROM graph_ingestion_runs
                    WHERE release_id = %s AND state = 'completed') AS completed_runs,
                (SELECT count(*) FROM graph_claims claim
                    WHERE claim.release_id = %s AND NOT EXISTS (
                        SELECT 1 FROM graph_evidence_links evidence
                        WHERE evidence.release_id = claim.release_id
                          AND evidence.claim_id = claim.id
                    )) AS claims_without_evidence,
                (SELECT count(*) FROM graph_relations relation
                    WHERE relation.release_id = %s AND NOT EXISTS (
                        SELECT 1 FROM graph_evidence_links evidence
                        WHERE evidence.release_id = relation.release_id
                          AND evidence.relation_id = relation.id
                    )) AS relations_without_evidence
            """,
            (release_id,) * 8,
        ).fetchone()
        if row is None:
            raise GraphRepositoryError("release integrity counts are unavailable")
        names = (
            "sources",
            "documents",
            "chunks",
            "running_runs",
            "failed_runs",
            "completed_runs",
            "claims_without_evidence",
            "relations_without_evidence",
        )
        return {
            name: int(_row_value(row, name, index) or 0)
            for index, name in enumerate(names)
        }

    def activate_release(
        self,
        deployment_scope: str,
        release_id: str,
        *,
        activated_by: str | None,
    ) -> ActivationResult:
        if deployment_scope not in {"internal", "pilot", "production"}:
            raise GraphIntegrityError("invalid deployment scope")
        with self._connection_factory() as connection:
            connection.execute(
                "SELECT pg_advisory_xact_lock(hashtext(%s))",
                (f"knowledge-activation:{deployment_scope}",),
            )
            release = connection.execute(
                """
                SELECT state, publication_scope, review_policy
                FROM knowledge_releases WHERE id = %s
                """,
                (release_id,),
            ).fetchone()
            if release is None or _row_value(release, "state", 0) != "ready":
                raise GraphIntegrityError("only a sealed ready release can be activated")
            publication_scope = _row_value(release, "publication_scope", 1)
            review_policy = _row_value(release, "review_policy", 2)
            if deployment_scope == "production" and (
                publication_scope != "production" or review_policy != "approved_only"
            ):
                raise GraphIntegrityError(
                    "production requires an approved-only production release"
                )
            if deployment_scope == "pilot" and publication_scope == "internal":
                raise GraphIntegrityError("internal releases cannot be activated for pilot")
            pointer = connection.execute(
                """
                SELECT release_id FROM active_knowledge_releases
                WHERE deployment_scope = %s FOR UPDATE
                """,
                (deployment_scope,),
            ).fetchone()
            previous = _row_value(pointer, "release_id", 0)
            if previous == release_id:
                return ActivationResult(deployment_scope, release_id, previous)
            connection.execute(
                """
                INSERT INTO knowledge_release_activations (
                    deployment_scope, release_id, previous_release_id,
                    activated_by, reason
                ) VALUES (%s, %s, %s, %s, 'activate')
                """,
                (deployment_scope, release_id, previous, activated_by),
            )
            connection.execute(
                """
                INSERT INTO active_knowledge_releases (
                    deployment_scope, release_id, activated_by
                ) VALUES (%s, %s, %s)
                ON CONFLICT (deployment_scope) DO UPDATE
                SET release_id = excluded.release_id,
                    activated_by = excluded.activated_by,
                    activated_at = now()
                """,
                (deployment_scope, release_id, activated_by),
            )
            return ActivationResult(deployment_scope, release_id, previous)

    def rollback_release(
        self,
        deployment_scope: str,
        *,
        activated_by: str | None,
    ) -> ActivationResult:
        """Atomically restore the release recorded before the current activation."""

        with self._connection_factory() as connection:
            connection.execute(
                "SELECT pg_advisory_xact_lock(hashtext(%s))",
                (f"knowledge-activation:{deployment_scope}",),
            )
            pointer = connection.execute(
                """
                SELECT release_id FROM active_knowledge_releases
                WHERE deployment_scope = %s FOR UPDATE
                """,
                (deployment_scope,),
            ).fetchone()
            current = _row_value(pointer, "release_id", 0)
            if current is None:
                raise GraphIntegrityError("deployment scope has no active release")
            activation = connection.execute(
                """
                SELECT previous_release_id
                FROM knowledge_release_activations
                WHERE deployment_scope = %s AND release_id = %s
                ORDER BY id DESC LIMIT 1
                """,
                (deployment_scope, current),
            ).fetchone()
            previous = _row_value(activation, "previous_release_id", 0)
            if previous is None:
                raise GraphIntegrityError("active release has no rollback target")
            ready = connection.execute(
                "SELECT state FROM knowledge_releases WHERE id = %s",
                (previous,),
            ).fetchone()
            if ready is None or _row_value(ready, "state", 0) != "ready":
                raise GraphIntegrityError("rollback target is not a ready release")
            connection.execute(
                """
                INSERT INTO knowledge_release_activations (
                    deployment_scope, release_id, previous_release_id,
                    activated_by, reason
                ) VALUES (%s, %s, %s, %s, 'rollback')
                """,
                (deployment_scope, previous, current, activated_by),
            )
            connection.execute(
                """
                UPDATE active_knowledge_releases
                SET release_id = %s, activated_by = %s, activated_at = now()
                WHERE deployment_scope = %s
                """,
                (previous, activated_by, deployment_scope),
            )
            return ActivationResult(
                deployment_scope,
                previous,
                current,
                rolled_back=True,
            )

    def active_release(self, deployment_scope: str) -> str | None:
        with self._connection_factory() as connection:
            row = connection.execute(
                """
                SELECT release_id FROM active_knowledge_releases
                WHERE deployment_scope = %s
                """,
                (deployment_scope,),
            ).fetchone()
            value = _row_value(row, "release_id", 0)
            return str(value) if value is not None else None

    def source_record(
        self,
        *,
        release_id: str,
        source_id: str,
    ) -> dict[str, Any] | None:
        """Return one release-scoped source register entry, by ID or key."""

        with self._connection_factory() as connection:
            row = connection.execute(
                """
                SELECT id, source_key, title, publisher, source_kind,
                       evidence_class, url, license, observed_at,
                       effective_from, expires_at, metadata_json
                FROM graph_sources
                WHERE release_id = %s AND (id = %s OR source_key = %s)
                LIMIT 1
                """,
                (release_id, source_id, source_id),
            ).fetchone()
            return dict(row) if row is not None else None

    def cached_embeddings(
        self,
        *,
        model: str,
        dimensions: int,
        input_type: str,
        content_hashes: Sequence[str],
    ) -> dict[str, tuple[float, ...]]:
        """Load reusable embeddings without crossing model/input configurations."""

        unique_hashes = list(dict.fromkeys(str(item) for item in content_hashes))
        if not unique_hashes:
            return {}
        with self._connection_factory() as connection:
            rows = connection.execute(
                """
                SELECT content_sha256, embedding::text AS embedding_text
                FROM graph_embedding_cache
                WHERE embedding_model = %s
                  AND embedding_dimensions = %s
                  AND input_type = %s
                  AND content_sha256 = ANY(%s::text[])
                """,
                (model, dimensions, input_type, unique_hashes),
            ).fetchall()
        result: dict[str, tuple[float, ...]] = {}
        for row in rows:
            digest = str(_row_value(row, "content_sha256", 0))
            vector = _vector_tuple(_row_value(row, "embedding_text", 1))
            if len(vector) != dimensions:
                raise GraphIntegrityError("cached embedding dimension mismatch")
            result[digest] = vector
        return result

    def cache_embeddings(
        self,
        *,
        model: str,
        dimensions: int,
        input_type: str,
        embeddings: Mapping[str, Sequence[float]],
    ) -> int:
        """Persist derived vectors idempotently for later release rebuilds."""

        if dimensions not in {384, 768, 1024, 1536}:
            raise GraphIntegrityError("unsupported embedding cache dimension")
        if input_type not in {"search_document", "search_query"}:
            raise GraphIntegrityError("unsupported embedding input type")
        with self._connection_factory() as connection:
            for digest, vector in embeddings.items():
                if (
                    len(digest) != 64
                    or any(character not in "0123456789abcdef" for character in digest)
                    or len(vector) != dimensions
                ):
                    raise GraphIntegrityError("embedding cache entry is invalid")
                connection.execute(
                    """
                    INSERT INTO graph_embedding_cache (
                        embedding_model, embedding_dimensions, input_type,
                        content_sha256, embedding
                    ) VALUES (%s, %s, %s, %s, %s::vector)
                    ON CONFLICT (
                        embedding_model, embedding_dimensions, input_type,
                        content_sha256
                    ) DO NOTHING
                    """,
                    (model, dimensions, input_type, digest, _vector(vector)),
                )
        return len(embeddings)

    def upsert_project_chunks(self, records: tuple[ProjectChunkRecord, ...]) -> int:
        """Persist private chunks only; no project graph rows are created."""

        validate_project_chunks(records)
        if not records:
            return 0
        with self._connection_factory() as connection:
            for record in records:
                connection.execute(
                    """
                    INSERT INTO project_rag_chunks (
                        owner_user_id, project_id, document_id, id, chunk_index,
                        language, content, normalized_content,
                        contextualized_content, content_sha256, embedding_model,
                        embedding_dimensions, embedding, metadata_json
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s::vector, %s::jsonb
                    ) ON CONFLICT (owner_user_id, id) DO NOTHING
                    """,
                    (
                        record.owner_user_id,
                        record.project_id,
                        record.document_id,
                        record.id,
                        record.chunk_index,
                        record.language,
                        record.content,
                        record.normalized_content,
                        record.contextualized_content,
                        record.content_hash,
                        record.embedding_model,
                        record.embedding_dimensions,
                        _vector(record.embedding),
                        _json(record.metadata),
                    ),
                )
        return len(records)

    def hybrid_search(
        self,
        *,
        release_id: str,
        query: str,
        embedding: Sequence[float] | None,
        embedding_model: str | None,
        embedding_dimensions: int | None,
        top_k: int,
        review_statuses: tuple[str, ...],
    ) -> list[dict[str, Any]]:
        with self._connection_factory() as connection:
            rows = connection.execute(
                """
                SELECT * FROM hybrid_search_knowledge_v2(
                    %s, %s, %s::vector, %s, %s, %s, %s::text[]
                )
                """,
                (
                    release_id,
                    query,
                    _vector(embedding),
                    embedding_model,
                    embedding_dimensions,
                    max(1, min(int(top_k), 50)),
                    list(review_statuses),
                ),
            ).fetchall()
            return [dict(row) for row in rows]

    def graph_paths(
        self,
        *,
        release_id: str,
        entity_ids: tuple[str, ...],
        max_hops: int,
        review_statuses: tuple[str, ...],
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Return bounded, evidence-backed, bidirectional paths up to two hops."""

        if not entity_ids:
            return []
        hops = max(1, min(int(max_hops), 2))
        with self._connection_factory() as connection:
            rows = connection.execute(
                """
                WITH RECURSIVE paths AS (
                    SELECT relation.id, relation.subject_entity_id,
                           relation.predicate, relation.object_entity_id,
                           relation.object_text, relation.review_status,
                           relation.risk, relation.geography_json,
                           1 AS depth,
                           CASE
                             WHEN relation.subject_entity_id = ANY(%s::text[])
                             THEN relation.object_entity_id
                             ELSE relation.subject_entity_id
                           END AS frontier_entity,
                           ARRAY[relation.subject_entity_id,
                                 relation.object_entity_id]::text[] AS entity_path
                    FROM graph_relations relation
                    WHERE relation.release_id = %s
                      AND (
                        relation.subject_entity_id = ANY(%s::text[])
                        OR relation.object_entity_id = ANY(%s::text[])
                      )
                      AND relation.review_status = ANY(%s::text[])
                      AND (relation.effective_from IS NULL OR relation.effective_from <= now())
                      AND (relation.expires_at IS NULL OR relation.expires_at > now())
                    UNION ALL
                    SELECT next.id, next.subject_entity_id, next.predicate,
                           next.object_entity_id, next.object_text,
                           next.review_status, next.risk,
                           next.geography_json, paths.depth + 1,
                           walk.next_entity,
                           paths.entity_path || walk.next_entity
                    FROM paths
                    JOIN graph_relations next
                      ON next.release_id = %s
                     AND (
                       next.subject_entity_id = paths.frontier_entity
                       OR next.object_entity_id = paths.frontier_entity
                     )
                    CROSS JOIN LATERAL (
                        SELECT CASE
                          WHEN next.subject_entity_id = paths.frontier_entity
                          THEN next.object_entity_id
                          ELSE next.subject_entity_id
                        END AS next_entity
                    ) walk
                    WHERE paths.depth < %s
                      AND next.review_status = ANY(%s::text[])
                      AND walk.next_entity IS NOT NULL
                      AND NOT walk.next_entity = ANY(paths.entity_path)
                      AND (next.effective_from IS NULL OR next.effective_from <= now())
                      AND (next.expires_at IS NULL OR next.expires_at > now())
                )
                SELECT paths.*,
                       coalesce(subject.label_en, subject.label_ar,
                                paths.subject_entity_id) AS subject_label,
                       coalesce(object.label_en, object.label_ar,
                                paths.object_entity_id) AS object_label,
                       array_agg(evidence.id ORDER BY evidence.id) AS evidence_ids,
                       array_agg(DISTINCT evidence.source_id) AS source_ids,
                       array_agg(DISTINCT evidence.chunk_id) AS passage_ids
                FROM paths
                JOIN graph_evidence_links evidence
                  ON evidence.release_id = %s
                 AND evidence.relation_id = paths.id
                LEFT JOIN graph_entities subject
                  ON subject.release_id = %s
                 AND subject.id = paths.subject_entity_id
                LEFT JOIN graph_entities object
                  ON object.release_id = %s
                 AND object.id = paths.object_entity_id
                GROUP BY paths.id, paths.subject_entity_id, paths.predicate,
                         paths.object_entity_id, paths.object_text,
                         paths.review_status, paths.risk, paths.geography_json,
                         paths.depth, paths.frontier_entity, paths.entity_path,
                         subject.label_en,
                         subject.label_ar, object.label_en, object.label_ar
                ORDER BY
                    CASE
                      WHEN paths.subject_entity_id = ANY(%s::text[])
                       AND paths.object_entity_id = ANY(%s::text[]) THEN 0
                      ELSE 1
                    END,
                    paths.depth, paths.id
                LIMIT %s
                """,
                (
                    list(entity_ids),
                    release_id,
                    list(entity_ids),
                    list(entity_ids),
                    list(review_statuses),
                    release_id,
                    hops,
                    list(review_statuses),
                    release_id,
                    release_id,
                    release_id,
                    list(entity_ids),
                    list(entity_ids),
                    max(1, min(int(limit), 100)),
                ),
            ).fetchall()
            return [dict(row) for row in rows]

    def resolve_entities(
        self,
        *,
        release_id: str,
        query: str,
        limit: int = 12,
    ) -> list[dict[str, Any]]:
        """Resolve deterministic multilingual aliases contained in a query."""

        normalized = normalize_search_text(query)
        if not normalized:
            return []
        with self._connection_factory() as connection:
            rows = connection.execute(
                """
                SELECT entity.id, entity.entity_type, entity.label_en,
                       entity.label_ar, alias.alias, alias.language
                FROM graph_entity_aliases alias
                JOIN graph_entities entity
                  ON entity.release_id = alias.release_id
                 AND entity.id = alias.entity_id
                WHERE alias.release_id = %s
                  AND strpos(
                    ' ' || %s || ' ',
                    ' ' || alias.normalized_alias || ' '
                  ) > 0
                ORDER BY length(alias.normalized_alias) DESC, entity.id
                LIMIT %s
                """,
                (release_id, normalized, max(1, min(int(limit), 30))),
            ).fetchall()
            return [dict(row) for row in rows]

    def hybrid_project_search(
        self,
        *,
        owner_user_id: str,
        project_id: str,
        query: str,
        embedding: Sequence[float] | None,
        embedding_model: str | None,
        embedding_dimensions: int | None,
        top_k: int,
    ) -> list[dict[str, Any]]:
        """Hybrid private retrieval with owner and project scope in every CTE."""

        with self._connection_factory() as connection:
            rows = connection.execute(
                """
                WITH eligible AS (
                    SELECT chunk.*, document.filename
                    FROM project_rag_chunks chunk
                    JOIN documents document
                      ON document.id = chunk.document_id
                     AND document.owner_user_id = chunk.owner_user_id
                     AND document.project_id = chunk.project_id
                    WHERE chunk.owner_user_id = %s AND chunk.project_id = %s
                ), lexical AS (
                    SELECT eligible.id,
                           row_number() OVER (
                             ORDER BY ts_rank_cd(
                               eligible.search_vector,
                               websearch_to_tsquery('simple', %s)
                             ) DESC, eligible.id
                           ) AS rank
                    FROM eligible
                    WHERE btrim(%s) <> ''
                      AND eligible.search_vector @@ websearch_to_tsquery('simple', %s)
                    LIMIT 40
                ), semantic AS (
                    SELECT eligible.id,
                           row_number() OVER (
                             ORDER BY eligible.embedding <=> %s::vector, eligible.id
                           ) AS rank
                    FROM eligible
                    WHERE %s::vector IS NOT NULL
                      AND eligible.embedding IS NOT NULL
                      AND eligible.embedding_model = %s
                      AND eligible.embedding_dimensions = %s
                    LIMIT 40
                ), fused AS (
                    SELECT coalesce(lexical.id, semantic.id) AS id,
                           lexical.rank AS lexical_rank,
                           semantic.rank AS semantic_rank,
                           coalesce(1.0 / (60 + lexical.rank), 0.0)
                           + coalesce(1.0 / (60 + semantic.rank), 0.0) AS score
                    FROM lexical FULL OUTER JOIN semantic
                      ON semantic.id = lexical.id
                )
                SELECT eligible.id AS chunk_id, eligible.document_id,
                       eligible.filename, eligible.content, eligible.language,
                       fused.lexical_rank, fused.semantic_rank, fused.score
                FROM fused JOIN eligible ON eligible.id = fused.id
                ORDER BY fused.score DESC, eligible.id
                LIMIT %s
                """,
                (
                    owner_user_id,
                    project_id,
                    query,
                    query,
                    query,
                    _vector(embedding),
                    _vector(embedding),
                    embedding_model,
                    embedding_dimensions,
                    max(1, min(int(top_k), 20)),
                ),
            ).fetchall()
            return [dict(row) for row in rows]
