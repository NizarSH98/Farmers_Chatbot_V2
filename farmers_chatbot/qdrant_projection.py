"""Versioned Qdrant projection for authoritative PostgreSQL knowledge releases."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import uuid
from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
from contextlib import AbstractContextManager
from dataclasses import asdict, dataclass
from typing import Any, Literal

import networkx as nx
from fastembed import SparseTextEmbedding, TextEmbedding
from fastembed.common.model_description import ModelSource, PoolingType
from qdrant_client import AsyncQdrantClient, models
from qdrant_client.http.exceptions import ApiException

from .arabizi import arabic_to_arabizi
from .graph_ingestion import normalize_search_text

ConnectionFactory = Callable[[], AbstractContextManager[Any]]
ProjectionState = Literal["pending", "building", "ready", "failed", "stale"]

_COLLECTION_SAFE = re.compile(r"[^a-zA-Z0-9_-]+")
_POINT_NAMESPACE = uuid.UUID("7a5a4aa3-8366-49dc-b76b-1a83fd366c2a")
_SUPPORTED_DIMENSIONS = frozenset({384, 768, 1024, 1536})
_CUSTOM_E5: Mapping[str, tuple[int, float]] = {
    "intfloat/multilingual-e5-small": (384, 0.47),
    "intfloat/multilingual-e5-base": (768, 1.12),
}


class ProjectionError(RuntimeError):
    """Raised when a Qdrant projection cannot be built or validated."""


@dataclass(frozen=True)
class ProjectionConfig:
    url: str
    api_key: str | None
    embedding_model: str
    embedding_dimensions: int
    cache_dir: str
    quantization: bool = True
    timeout_seconds: int = 30
    batch_size: int = 64

    @classmethod
    def from_env(cls) -> ProjectionConfig:
        dimensions = int(os.getenv("RAG_LOCAL_EMBEDDING_DIMENSIONS", "384"))
        if dimensions not in _SUPPORTED_DIMENSIONS:
            raise ProjectionError("unsupported local embedding dimensions")
        return cls(
            url=os.getenv("QDRANT_URL", "http://localhost:6433").rstrip("/"),
            api_key=os.getenv("QDRANT_API_KEY") or None,
            embedding_model=os.getenv(
                "RAG_LOCAL_EMBEDDING_MODEL",
                "intfloat/multilingual-e5-small",
            ),
            embedding_dimensions=dimensions,
            cache_dir=os.getenv("RAG_MODEL_CACHE", "model-cache"),
            quantization=os.getenv("RAG_ENABLE_QUANTIZATION", "true").lower()
            == "true",
            timeout_seconds=max(3, int(os.getenv("QDRANT_TIMEOUT_SECONDS", "10"))),
        )


@dataclass(frozen=True)
class ProjectionManifest:
    release_id: str
    evidence_collection: str
    entity_collection: str
    evidence_points: int
    entity_points: int
    embedding_model: str
    embedding_dimensions: int
    manifest_sha256: str


@dataclass(frozen=True)
class ProjectionPoint:
    source_id: str
    kind: str
    text: str
    language: str
    payload: dict[str, Any]

    @property
    def point_uuid(self) -> str:
        return str(uuid.uuid5(_POINT_NAMESPACE, f"{self.kind}:{self.source_id}"))


def collection_names(release_id: str) -> tuple[str, str]:
    safe = _COLLECTION_SAFE.sub("-", release_id).strip("-")[:120]
    if not safe:
        raise ProjectionError("release ID cannot form a Qdrant collection name")
    return f"raise_evidence__{safe}", f"raise_entities__{safe}"


def projection_manifest_hash(points: Iterable[ProjectionPoint]) -> str:
    canonical = [
        {
            "point_uuid": point.point_uuid,
            "source_id": point.source_id,
            "kind": point.kind,
            "text_sha256": hashlib.sha256(point.text.encode("utf-8")).hexdigest(),
            "payload": point.payload,
        }
        for point in points
    ]
    canonical.sort(key=lambda item: item["point_uuid"])
    encoded = json.dumps(
        canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def projection_search_text(text: str, language: str) -> str:
    """Add a deterministic cross-script field while retaining authoritative text."""

    if not language.lower().startswith("ar"):
        return text
    transliterated = arabic_to_arabizi(text)
    return f"{text}\n{transliterated}" if transliterated else text


class LocalEmbeddingService:
    """Pinned local dense and language-specific BM25 encoders."""

    def __init__(self, config: ProjectionConfig) -> None:
        self.config = config
        self._dense: TextEmbedding | None = None
        self._sparse: dict[str, SparseTextEmbedding] = {}

    def _dense_model(self) -> TextEmbedding:
        if self._dense is not None:
            return self._dense
        custom = _CUSTOM_E5.get(self.config.embedding_model)
        if custom:
            dimensions, size_gb = custom
            if dimensions != self.config.embedding_dimensions:
                raise ProjectionError("configured E5 dimension does not match model")
            try:
                TextEmbedding.add_custom_model(
                    model=self.config.embedding_model,
                    pooling=PoolingType.MEAN,
                    normalization=True,
                    sources=ModelSource(hf=self.config.embedding_model),
                    dim=dimensions,
                    model_file="onnx/model.onnx",
                    description="Pinned multilingual E5 retrieval model",
                    license="mit",
                    size_in_gb=size_gb,
                )
            except ValueError:
                pass
        try:
            model = TextEmbedding(
                self.config.embedding_model,
                cache_dir=self.config.cache_dir,
                threads=max(1, min((os.cpu_count() or 2) // 2, 8)),
            )
        except Exception as exc:
            raise ProjectionError(
                f"local embedding model is unavailable: {self.config.embedding_model}"
            ) from exc
        probe = next(iter(model.embed(["query: RAISE model dimension probe"])))
        if len(probe) != self.config.embedding_dimensions:
            raise ProjectionError("local embedding output dimension mismatch")
        self._dense = model
        return model

    def _sparse_model(self, language: str) -> SparseTextEmbedding:
        key = "arabic" if language.lower().startswith("ar") else "english"
        if key not in self._sparse:
            self._sparse[key] = SparseTextEmbedding(
                "Qdrant/bm25",
                cache_dir=self.config.cache_dir,
                language=key,
            )
        return self._sparse[key]

    @staticmethod
    def _e5_prefix(text: str, *, query: bool, model: str) -> str:
        if "e5" not in model.lower():
            return text
        return f"{'query' if query else 'passage'}: {text}"

    def dense(self, texts: Sequence[str], *, query: bool = False) -> list[list[float]]:
        prepared = [
            self._e5_prefix(text, query=query, model=self.config.embedding_model)
            for text in texts
        ]
        return [vector.tolist() for vector in self._dense_model().embed(prepared)]

    def sparse(
        self,
        texts: Sequence[str],
        languages: Sequence[str],
    ) -> list[models.SparseVector]:
        if len(texts) != len(languages):
            raise ProjectionError("sparse text/language batch length mismatch")
        output: list[models.SparseVector | None] = [None] * len(texts)
        groups: dict[str, list[int]] = defaultdict(list)
        for index, language in enumerate(languages):
            groups["arabic" if language.lower().startswith("ar") else "english"].append(
                index
            )
        for language, indexes in groups.items():
            vectors = self._sparse_model(language).embed([texts[index] for index in indexes])
            for index, vector in zip(indexes, vectors, strict=True):
                output[index] = models.SparseVector(
                    indices=vector.indices.tolist(), values=vector.values.tolist()
                )
        if any(vector is None for vector in output):
            raise ProjectionError("sparse encoder returned an incomplete batch")
        return [vector for vector in output if vector is not None]


class QdrantProjectionRepository:
    """PostgreSQL projection metadata and immutable release export."""

    def __init__(self, connection_factory: ConnectionFactory) -> None:
        self._connection_factory = connection_factory

    def release(self, release_id: str) -> dict[str, Any]:
        with self._connection_factory() as connection:
            row = connection.execute(
                """
                SELECT id, version, state, publication_scope, review_policy,
                       embedding_model, embedding_dimensions, source_manifest_sha256
                FROM knowledge_releases WHERE id = %s
                """,
                (release_id,),
            ).fetchone()
        if not row:
            raise ProjectionError("knowledge release does not exist")
        result = dict(row)
        if result["state"] != "ready":
            raise ProjectionError("only a sealed release can be projected")
        return result

    def set_state(
        self,
        release_id: str,
        config: ProjectionConfig,
        state: ProjectionState,
        *,
        manifest: ProjectionManifest | None = None,
        error: str | None = None,
    ) -> None:
        evidence, entities = collection_names(release_id)
        with self._connection_factory() as connection:
            connection.execute(
                """
                INSERT INTO knowledge_release_projections (
                    release_id, target, state, evidence_collection,
                    entity_collection, embedding_model, embedding_dimensions,
                    started_at, updated_at
                ) VALUES (%s, 'qdrant', %s, %s, %s, %s, %s,
                          CASE WHEN %s = 'building' THEN now() END, now())
                ON CONFLICT (release_id, target) DO UPDATE SET
                    state = excluded.state,
                    evidence_collection = excluded.evidence_collection,
                    entity_collection = excluded.entity_collection,
                    embedding_model = excluded.embedding_model,
                    embedding_dimensions = excluded.embedding_dimensions,
                    started_at = CASE WHEN excluded.state = 'building'
                        THEN now() ELSE knowledge_release_projections.started_at END,
                    manifest_sha256 = %s,
                    evidence_points = %s,
                    entity_points = %s,
                    last_error = %s,
                    ready_at = CASE WHEN excluded.state = 'ready'
                        THEN now() ELSE knowledge_release_projections.ready_at END,
                    updated_at = now()
                """,
                (
                    release_id,
                    state,
                    evidence,
                    entities,
                    config.embedding_model,
                    config.embedding_dimensions,
                    state,
                    manifest.manifest_sha256 if manifest else None,
                    manifest.evidence_points if manifest else 0,
                    manifest.entity_points if manifest else 0,
                    (error or "")[:2000] or None,
                ),
            )
            outbox_state = {
                "building": "processing",
                "ready": "completed",
                "failed": "failed",
                "stale": "pending",
                "pending": "pending",
            }[state]
            connection.execute(
                """
                UPDATE knowledge_projection_outbox
                SET state = %s,
                    attempts = attempts + CASE WHEN %s = 'building' THEN 1 ELSE 0 END,
                    last_error = %s,
                    completed_at = CASE WHEN %s = 'ready' THEN now() ELSE NULL END,
                    available_at = CASE WHEN %s = 'failed'
                        THEN now() + interval '30 seconds' ELSE available_at END
                WHERE release_id = %s AND event_type = 'project'
                """,
                (outbox_state, state, (error or "")[:2000] or None, state, state, release_id),
            )

    def projection(self, release_id: str) -> dict[str, Any] | None:
        with self._connection_factory() as connection:
            row = connection.execute(
                """
                SELECT * FROM knowledge_release_projections
                WHERE release_id = %s AND target = 'qdrant'
                """,
                (release_id,),
            ).fetchone()
        return dict(row) if row else None

    def reserve_outbox(self, *, limit: int = 10) -> list[str]:
        """Atomically reserve pending/failed projection work for one worker."""

        with self._connection_factory() as connection:
            rows = connection.execute(
                """
                WITH candidates AS (
                    SELECT id FROM knowledge_projection_outbox
                    WHERE event_type = 'project'
                      AND state IN ('pending', 'failed')
                      AND available_at <= now()
                    ORDER BY id
                    FOR UPDATE SKIP LOCKED
                    LIMIT %s
                )
                UPDATE knowledge_projection_outbox outbox
                SET state = 'processing'
                FROM candidates
                WHERE outbox.id = candidates.id
                RETURNING outbox.release_id
                """,
                (max(1, min(limit, 100)),),
            ).fetchall()
        return [str(row["release_id"]) for row in rows]

    def compute_metrics(self, release_id: str) -> dict[str, dict[str, Any]]:
        with self._connection_factory() as connection:
            entity_rows = connection.execute(
                "SELECT id FROM graph_entities WHERE release_id = %s", (release_id,)
            ).fetchall()
            relation_rows = connection.execute(
                """
                SELECT id, subject_entity_id, object_entity_id
                FROM graph_relations
                WHERE release_id = %s AND object_entity_id IS NOT NULL
                """,
                (release_id,),
            ).fetchall()
            evidence_rows = connection.execute(
                """
                SELECT relation_id, count(*) AS evidence_count
                FROM graph_evidence_links
                WHERE release_id = %s AND relation_id IS NOT NULL
                GROUP BY relation_id
                """,
                (release_id,),
            ).fetchall()
        graph = nx.DiGraph()
        graph.add_nodes_from(str(row["id"]) for row in entity_rows)
        evidence_by_relation = {
            str(row["relation_id"]): int(row["evidence_count"])
            for row in evidence_rows
        }
        entity_evidence: dict[str, int] = defaultdict(int)
        for row in relation_rows:
            subject = str(row["subject_entity_id"])
            target = str(row["object_entity_id"])
            graph.add_edge(subject, target)
            count = evidence_by_relation.get(str(row["id"]), 0)
            entity_evidence[subject] += count
            entity_evidence[target] += count
        ranks = nx.pagerank(graph) if graph.number_of_nodes() else {}
        components = list(nx.weakly_connected_components(graph))
        component_ids = {
            entity: f"component-{index:04d}"
            for index, component in enumerate(
                sorted(components, key=lambda item: min(item) if item else "")
            )
            for entity in component
        }
        metrics = {
            node: {
                "pagerank_global": float(ranks.get(node, 0.0)),
                "degree": int(graph.degree(node)),
                "evidence_count": int(entity_evidence.get(node, 0)),
                "component_id": component_ids.get(node),
            }
            for node in graph.nodes
        }
        with self._connection_factory() as connection:
            connection.execute(
                "DELETE FROM graph_entity_metrics WHERE release_id = %s", (release_id,)
            )
            for entity_id, values in metrics.items():
                connection.execute(
                    """
                    INSERT INTO graph_entity_metrics (
                        release_id, entity_id, pagerank_global, degree,
                        evidence_count, component_id
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        release_id,
                        entity_id,
                        values["pagerank_global"],
                        values["degree"],
                        values["evidence_count"],
                        values["component_id"],
                    ),
                )
        return metrics

    def points(self, release_id: str) -> tuple[list[ProjectionPoint], list[ProjectionPoint]]:
        with self._connection_factory() as connection:
            chunk_rows = connection.execute(
                """
                SELECT chunk.id, chunk.document_id, chunk.source_id,
                       chunk.section_path, chunk.language, chunk.content,
                       chunk.normalized_content, chunk.content_sha256,
                       chunk.review_status, chunk.risk, chunk.geography_json,
                       chunk.metadata_json, document.content_sha256 AS document_hash,
                       array_remove(array_agg(DISTINCT entity.canonical_key), NULL)
                           AS entity_keys
                FROM graph_chunks chunk
                JOIN graph_documents document
                  ON document.release_id = chunk.release_id
                 AND document.id = chunk.document_id
                LEFT JOIN graph_evidence_links evidence
                  ON evidence.release_id = chunk.release_id
                 AND evidence.chunk_id = chunk.id
                LEFT JOIN graph_relations relation
                  ON relation.release_id = evidence.release_id
                 AND relation.id = evidence.relation_id
                LEFT JOIN graph_entities entity
                  ON entity.release_id = relation.release_id
                 AND entity.id IN (
                    relation.subject_entity_id, relation.object_entity_id
                 )
                WHERE chunk.release_id = %s AND document.retrieval_enabled
                GROUP BY chunk.id, chunk.document_id, chunk.source_id,
                         chunk.section_path, chunk.language, chunk.content,
                         chunk.normalized_content, chunk.content_sha256,
                         chunk.review_status, chunk.risk, chunk.geography_json,
                         chunk.metadata_json, document.content_sha256
                ORDER BY chunk.id
                """,
                (release_id,),
            ).fetchall()
            claim_rows = connection.execute(
                """
                SELECT claim.id, claim.claim_text, claim.language,
                       claim.content_sha256, claim.review_status, claim.risk,
                       claim.geography_json, claim.metadata_json,
                       claim.effective_from, claim.expires_at,
                       array_agg(DISTINCT evidence.source_id) AS source_ids,
                       min(evidence.excerpt) AS evidence_excerpt
                FROM graph_claims claim
                JOIN graph_evidence_links evidence
                  ON evidence.release_id = claim.release_id
                 AND evidence.claim_id = claim.id
                WHERE claim.release_id = %s
                GROUP BY claim.id, claim.claim_text, claim.language,
                         claim.content_sha256, claim.review_status, claim.risk,
                         claim.geography_json, claim.metadata_json,
                         claim.effective_from, claim.expires_at
                ORDER BY claim.id
                """,
                (release_id,),
            ).fetchall()
            entity_rows = connection.execute(
                """
                SELECT entity.id, entity.entity_type, entity.canonical_key,
                       entity.label_en, entity.label_ar, entity.description,
                       entity.metadata_json,
                       coalesce(metric.pagerank_global, 0) AS pagerank_global,
                       coalesce(metric.degree, 0) AS degree,
                       coalesce(metric.evidence_count, 0) AS evidence_count,
                       metric.component_id,
                       jsonb_agg(jsonb_build_object(
                           'language', alias.language, 'script', alias.script,
                           'alias', alias.alias, 'normalized', alias.normalized_alias
                       ) ORDER BY alias.language, alias.normalized_alias)
                           FILTER (WHERE alias.entity_id IS NOT NULL) AS aliases
                FROM graph_entities entity
                LEFT JOIN graph_entity_metrics metric
                  ON metric.release_id = entity.release_id
                 AND metric.entity_id = entity.id
                LEFT JOIN graph_entity_aliases alias
                  ON alias.release_id = entity.release_id
                 AND alias.entity_id = entity.id
                WHERE entity.release_id = %s
                GROUP BY entity.id, entity.entity_type, entity.canonical_key,
                         entity.label_en, entity.label_ar, entity.description,
                         entity.metadata_json, metric.pagerank_global,
                         metric.degree, metric.evidence_count, metric.component_id
                ORDER BY entity.id
                """,
                (release_id,),
            ).fetchall()

        evidence_points: list[ProjectionPoint] = []
        for row in chunk_rows:
            metadata = dict(row.get("metadata_json") or {})
            language = str(row["language"])
            content = str(row["content"])
            evidence_points.append(
                ProjectionPoint(
                    source_id=f"{release_id}:chunk:{row['id']}",
                    kind="chunk",
                    text=projection_search_text(content, language),
                    language=language,
                    payload={
                        "release_id": release_id,
                        "record_type": "chunk",
                        "record_id": str(row["id"]),
                        "document_id": str(row["document_id"]),
                        "document_hash": str(row["document_hash"]),
                        "chunk_hash": str(row["content_sha256"]),
                        "entity_keys": list(row.get("entity_keys") or []),
                        "source_ids": [str(row["source_id"])],
                        "language": language,
                        "geography": list(row.get("geography_json") or []),
                        "topics": list(metadata.get("topics") or []),
                        "risk": str(row["risk"]),
                        "review_status": str(row["review_status"]),
                        "section_path": str(row["section_path"] or ""),
                        "content": content,
                        "normalized_content": str(row["normalized_content"]),
                        "content_en": content if language.lower().startswith("en") else "",
                        "content_ar": content if language.lower().startswith("ar") else "",
                        "content_arabizi": (
                            arabic_to_arabizi(content)
                            if language.lower().startswith("ar") else ""
                        ),
                        "pagerank_global": 0.0,
                        "evidence_count": 1,
                    },
                )
            )
        for row in claim_rows:
            language = str(row["language"])
            content = str(row["claim_text"])
            metadata = dict(row.get("metadata_json") or {})
            evidence_points.append(
                ProjectionPoint(
                    source_id=f"{release_id}:claim:{row['id']}",
                    kind="claim",
                    text=projection_search_text(content, language),
                    language=language,
                    payload={
                        "release_id": release_id,
                        "record_type": "claim",
                        "record_id": str(row["id"]),
                        "document_id": "",
                        "document_hash": "",
                        "chunk_hash": str(row["content_sha256"]),
                        "entity_keys": list(metadata.get("entity_keys") or []),
                        "source_ids": [str(value) for value in row["source_ids"]],
                        "language": language,
                        "geography": list(row.get("geography_json") or []),
                        "topics": list(metadata.get("topics") or []),
                        "risk": str(row["risk"]),
                        "review_status": str(row["review_status"]),
                        "effective_from": row.get("effective_from"),
                        "expires_at": row.get("expires_at"),
                        "content": content,
                        "normalized_content": normalize_search_text(content),
                        "content_en": content if language.lower().startswith("en") else "",
                        "content_ar": content if language.lower().startswith("ar") else "",
                        "content_arabizi": (
                            arabic_to_arabizi(content)
                            if language.lower().startswith("ar") else ""
                        ),
                        "evidence_excerpt": str(row["evidence_excerpt"] or ""),
                        "pagerank_global": 0.0,
                        "evidence_count": len(row["source_ids"]),
                    },
                )
            )

        entity_points: list[ProjectionPoint] = []
        for row in entity_rows:
            aliases = list(row.get("aliases") or [])
            labels = [str(row.get("label_en") or ""), str(row.get("label_ar") or "")]
            labels.extend(str(alias.get("alias") or "") for alias in aliases)
            text = " | ".join(dict.fromkeys(value for value in labels if value))
            entity_arabizi = arabic_to_arabizi(str(row.get("label_ar") or ""))
            search_text = f"{text} | {entity_arabizi}" if entity_arabizi else text
            language = "ar" if row.get("label_ar") and not row.get("label_en") else "multi"
            entity_points.append(
                ProjectionPoint(
                    source_id=f"{release_id}:entity:{row['id']}",
                    kind="entity",
                    text=search_text,
                    language=language,
                    payload={
                        "release_id": release_id,
                        "record_type": "entity",
                        "record_id": str(row["id"]),
                        "entity_key": str(row["canonical_key"]),
                        "entity_type": str(row["entity_type"]),
                        "entity_keys": [str(row["canonical_key"])],
                        "language": language,
                        "aliases": aliases,
                        "content": text,
                        "normalized_content": normalize_search_text(text),
                        "content_en": str(row.get("label_en") or ""),
                        "content_ar": str(row.get("label_ar") or ""),
                        "content_arabizi": entity_arabizi,
                        "pagerank_global": float(row["pagerank_global"]),
                        "degree": int(row["degree"]),
                        "evidence_count": int(row["evidence_count"]),
                        "component_id": row.get("component_id"),
                    },
                )
            )
        return evidence_points, entity_points


class QdrantProjector:
    def __init__(
        self,
        repository: QdrantProjectionRepository,
        config: ProjectionConfig,
        *,
        client: AsyncQdrantClient | None = None,
        embeddings: LocalEmbeddingService | None = None,
    ) -> None:
        self.repository = repository
        self.config = config
        self.client = client or AsyncQdrantClient(
            url=config.url,
            api_key=config.api_key,
            timeout=config.timeout_seconds,
        )
        self.embeddings = embeddings or LocalEmbeddingService(config)

    async def close(self) -> None:
        await self.client.close()

    async def health(self) -> bool:
        try:
            await self.client.get_collections()
            return True
        except (ApiException, OSError, TimeoutError):
            return False

    async def project(self, release_id: str) -> ProjectionManifest:
        release = await asyncio.to_thread(self.repository.release, release_id)
        if release["embedding_model"] != self.config.embedding_model or int(
            release["embedding_dimensions"]
        ) != self.config.embedding_dimensions:
            raise ProjectionError("release embedding configuration differs from Qdrant")
        existing = await asyncio.to_thread(self.repository.projection, release_id)
        if existing and existing["state"] == "ready":
            manifest = ProjectionManifest(
                release_id=release_id,
                evidence_collection=existing["evidence_collection"],
                entity_collection=existing["entity_collection"],
                evidence_points=int(existing["evidence_points"]),
                entity_points=int(existing["entity_points"]),
                embedding_model=existing["embedding_model"],
                embedding_dimensions=int(existing["embedding_dimensions"]),
                manifest_sha256=existing["manifest_sha256"],
            )
            collections_exist = await asyncio.gather(
                self.client.collection_exists(manifest.evidence_collection),
                self.client.collection_exists(manifest.entity_collection),
            )
            if all(collections_exist):
                try:
                    await self._validate_count(manifest.evidence_collection, manifest.evidence_points)
                    await self._validate_count(manifest.entity_collection, manifest.entity_points)
                    return manifest
                except ProjectionError:
                    pass
            await asyncio.to_thread(
                self.repository.set_state, release_id, self.config, "stale",
                error="ready projection is missing or count-mismatched",
            )
        await asyncio.to_thread(
            self.repository.set_state, release_id, self.config, "building"
        )
        evidence_collection, entity_collection = collection_names(release_id)
        try:
            await asyncio.to_thread(self.repository.compute_metrics, release_id)
            evidence_points, entity_points = await asyncio.to_thread(
                self.repository.points, release_id
            )
            all_points = [*evidence_points, *entity_points]
            manifest_hash = projection_manifest_hash(all_points)
            await self._recreate_collection(evidence_collection)
            await self._recreate_collection(entity_collection)
            await self._upload(evidence_collection, evidence_points)
            await self._upload(entity_collection, entity_points)
            await self._validate_count(evidence_collection, len(evidence_points))
            await self._validate_count(entity_collection, len(entity_points))
            manifest = ProjectionManifest(
                release_id=release_id,
                evidence_collection=evidence_collection,
                entity_collection=entity_collection,
                evidence_points=len(evidence_points),
                entity_points=len(entity_points),
                embedding_model=self.config.embedding_model,
                embedding_dimensions=self.config.embedding_dimensions,
                manifest_sha256=manifest_hash,
            )
            await asyncio.to_thread(
                self.repository.set_state,
                release_id,
                self.config,
                "ready",
                manifest=manifest,
            )
            return manifest
        except Exception as exc:
            await asyncio.gather(
                self._delete_if_exists(evidence_collection),
                self._delete_if_exists(entity_collection),
            )
            await asyncio.to_thread(
                self.repository.set_state,
                release_id,
                self.config,
                "failed",
                error=f"{type(exc).__name__}: {exc}",
            )
            raise ProjectionError(f"Qdrant projection failed for {release_id}") from exc

    async def _delete_if_exists(self, collection: str) -> None:
        if await self.client.collection_exists(collection):
            await self.client.delete_collection(collection, timeout=self.config.timeout_seconds)

    async def _recreate_collection(self, collection: str) -> None:
        if await self.client.collection_exists(collection):
            await self.client.delete_collection(collection, timeout=self.config.timeout_seconds)
        quantization = None
        if self.config.quantization:
            quantization = models.ScalarQuantization(
                scalar=models.ScalarQuantizationConfig(
                    type=models.ScalarType.INT8, quantile=0.99, always_ram=True
                )
            )
        await self.client.create_collection(
            collection_name=collection,
            vectors_config={
                "dense": models.VectorParams(
                    size=self.config.embedding_dimensions,
                    distance=models.Distance.COSINE,
                    on_disk=False,
                )
            },
            sparse_vectors_config={
                "bm25": models.SparseVectorParams(modifier=models.Modifier.IDF)
            },
            quantization_config=quantization,
            on_disk_payload=True,
            timeout=self.config.timeout_seconds,
        )
        keyword_fields = (
            "release_id", "record_type", "record_id", "document_id", "language",
            "risk", "review_status", "entity_keys", "source_ids", "topics",
            "geography", "entity_key", "entity_type", "component_id",
        )
        for field in keyword_fields:
            await self.client.create_payload_index(
                collection, field, models.PayloadSchemaType.KEYWORD, wait=True
            )
        for field in ("evidence_count", "degree"):
            await self.client.create_payload_index(
                collection, field, models.PayloadSchemaType.INTEGER, wait=True
            )
        await self.client.create_payload_index(
            collection,
            "content_en",
            models.TextIndexParams(
                type=models.TextIndexType.TEXT,
                tokenizer=models.TokenizerType.WORD,
                lowercase=True,
                phrase_matching=True,
                stopwords=models.Language.ENGLISH,
                stemmer=models.SnowballParams(
                    type=models.Snowball.SNOWBALL,
                    language=models.SnowballLanguage.ENGLISH,
                ),
            ),
            wait=True,
        )
        await self.client.create_payload_index(
            collection,
            "content_ar",
            models.TextIndexParams(
                type=models.TextIndexType.TEXT,
                tokenizer=models.TokenizerType.MULTILINGUAL,
                lowercase=True,
                phrase_matching=True,
                stopwords=models.Language.ARABIC,
                stemmer=models.SnowballParams(
                    type=models.Snowball.SNOWBALL,
                    language=models.SnowballLanguage.ARABIC,
                ),
            ),
            wait=True,
        )
        await self.client.create_payload_index(
            collection,
            "content_arabizi",
            models.TextIndexParams(
                type=models.TextIndexType.TEXT,
                tokenizer=models.TokenizerType.WORD,
                lowercase=True,
                phrase_matching=True,
            ),
            wait=True,
        )
        await self.client.create_payload_index(
            collection,
            "normalized_content",
            models.TextIndexParams(
                type=models.TextIndexType.TEXT,
                tokenizer=models.TokenizerType.MULTILINGUAL,
                lowercase=True,
                phrase_matching=True,
            ),
            wait=True,
        )

    async def _upload(
        self, collection: str, points: Sequence[ProjectionPoint]
    ) -> None:
        for start in range(0, len(points), self.config.batch_size):
            batch = points[start : start + self.config.batch_size]
            dense = await asyncio.to_thread(
                self.embeddings.dense, [point.text for point in batch]
            )
            sparse = await asyncio.to_thread(
                self.embeddings.sparse,
                [point.text for point in batch],
                [point.language for point in batch],
            )
            qdrant_points = []
            for point, dense_vector, sparse_vector in zip(
                batch, dense, sparse, strict=True
            ):
                payload = {**point.payload, "point_uuid": point.point_uuid}
                qdrant_points.append(
                    models.PointStruct(
                        id=point.point_uuid,
                        vector={"dense": dense_vector, "bm25": sparse_vector},
                        payload=payload,
                    )
                )
            await self.client.upsert(
                collection_name=collection, points=qdrant_points, wait=True
            )

    async def _validate_count(self, collection: str, expected: int) -> None:
        result = await self.client.count(collection, exact=True)
        if result.count != expected:
            raise ProjectionError(
                f"Qdrant count mismatch for {collection}: {result.count} != {expected}"
            )

    async def activate_aliases(self, manifest: ProjectionManifest) -> None:
        aliases = {alias.alias_name for alias in (await self.client.get_aliases()).aliases}
        operations: list[Any] = []
        for alias, collection in (
            ("raise_evidence_active", manifest.evidence_collection),
            ("raise_entities_active", manifest.entity_collection),
        ):
            if alias in aliases:
                operations.append(
                    models.DeleteAliasOperation(
                        delete_alias=models.DeleteAlias(alias_name=alias)
                    )
                )
            operations.append(
                models.CreateAliasOperation(
                    create_alias=models.CreateAlias(
                        collection_name=collection, alias_name=alias
                    )
                )
            )
        await self.client.update_collection_aliases(operations)

    async def reconcile(self, *, limit: int = 10) -> list[ProjectionManifest]:
        """Repair reserved projections without changing the active pointer."""

        release_ids = await asyncio.to_thread(
            self.repository.reserve_outbox, limit=limit
        )
        manifests: list[ProjectionManifest] = []
        for release_id in release_ids:
            try:
                manifests.append(await self.project(release_id))
            except ProjectionError:
                # Failure details and bounded retry time are already persisted.
                continue
        return manifests


def manifest_as_dict(manifest: ProjectionManifest) -> dict[str, Any]:
    return asdict(manifest)
