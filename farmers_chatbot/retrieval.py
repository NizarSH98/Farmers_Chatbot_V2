"""Stable retrieval contract and legacy hybrid adapter."""

from __future__ import annotations

import asyncio
import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

import httpx

try:  # PostgreSQL support is optional in local/SQLite development.
    from psycopg import Error as PsycopgError
except ModuleNotFoundError:
    class PsycopgError(Exception):
        """Placeholder used only when the optional PostgreSQL driver is absent."""

from .documents import ProjectSearchResult, search_project_chunks
from .graph_repository import GraphRepository, GraphRepositoryError
from .knowledge import KnowledgeIndex, SearchResult
from .provider import ProviderClient


@dataclass(frozen=True)
class RetrievalRequest:
    query: str
    language: str
    mode: str
    queries: tuple[str, ...] = ()
    actor_id: str | None = None
    project_id: str | None = None
    geography: str | None = None
    domain: str | None = None
    risk: str = "medium"
    currentness: str = "stable"
    top_k: int = 6
    graph_hops: int = 1
    route_override: str | None = None
    release_pin: str | None = None


@dataclass(frozen=True)
class EvidenceItem:
    evidence_id: str
    source_type: str
    title: str
    excerpt: str
    language: str | None
    review_status: str
    source_ids: tuple[str, ...] = ()
    geography: tuple[str, ...] = ()
    risk: str = "medium"
    scores: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def citation(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "source_type": self.source_type,
            "title": self.title,
            "excerpt": self.excerpt,
            "language": self.language,
            "review_status": self.review_status,
            "status": self.review_status,
            "source_ids": list(self.source_ids),
            "geography": list(self.geography),
            "risk": self.risk,
        }


@dataclass
class EvidenceBundle:
    passages: list[EvidenceItem] = field(default_factory=list)
    claims: list[EvidenceItem] = field(default_factory=list)
    graph_paths: list[dict[str, Any]] = field(default_factory=list)
    live_evidence: list[EvidenceItem] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    retrieval_metrics: dict[str, Any] = field(default_factory=dict)
    knowledge_results: list[SearchResult] = field(default_factory=list)
    project_results: list[ProjectSearchResult] = field(default_factory=list)
    release_id: str | None = None
    retrieval_route: str | None = None
    ranking_channels: list[str] = field(default_factory=list)
    projection_status: str | None = None


class RetrievalService:
    async def retrieve(
        self,
        request: RetrievalRequest,
        *,
        project_chunks: list[dict[str, Any]] | None = None,
    ) -> EvidenceBundle:
        raise NotImplementedError


class LegacyHybridRetrieval(RetrievalService):
    """RRF over all analyzer query variants using the current local indexes."""

    def __init__(self, knowledge: KnowledgeIndex, *, rrf_k: int = 60) -> None:
        self.knowledge = knowledge
        self.rrf_k = max(1, rrf_k)

    async def retrieve(
        self,
        request: RetrievalRequest,
        *,
        project_chunks: list[dict[str, Any]] | None = None,
    ) -> EvidenceBundle:
        queries = tuple(dict.fromkeys((request.query, *request.queries)))[:4]
        top_candidates = max(request.top_k * 2, request.top_k)
        knowledge_runs = await asyncio.gather(
            *(
                asyncio.to_thread(
                    self.knowledge.search,
                    query,
                    language=request.language,
                    top_k=top_candidates,
                )
                for query in queries
            )
        )
        allowed_statuses = self._review_statuses(request)
        knowledge_runs = [
            [item for item in run if item.status in allowed_statuses]
            for run in knowledge_runs
        ]
        project_runs: list[list[ProjectSearchResult]] = []
        if project_chunks:
            project_runs = list(
                await asyncio.gather(
                    *(
                        asyncio.to_thread(
                            search_project_chunks,
                            project_chunks,
                            query,
                            top_k=min(8, top_candidates),
                        )
                        for query in queries
                    )
                )
            )
        knowledge_results, knowledge_scores = self._fuse_knowledge(
            knowledge_runs, request.top_k
        )
        project_results, project_scores = self._fuse_projects(
            project_runs, min(5, request.top_k)
        )
        passages = [
            EvidenceItem(
                evidence_id=f"kb:{item.item_id}:{item.language}",
                source_type="internal_knowledge",
                title=item.title,
                excerpt=item.text,
                language=item.language,
                review_status=item.status,
                source_ids=item.source_ids,
                geography=item.geography,
                risk=item.risk,
                scores={"rrf": knowledge_scores[item.item_id]},
                metadata={"item_id": item.item_id},
            )
            for item in knowledge_results
        ]
        passages.extend(
            EvidenceItem(
                evidence_id=f"project:{item.document_id}:{item.chunk_id}",
                source_type="project_document",
                title=item.filename,
                excerpt=item.text,
                language=None,
                review_status="user_provided",
                scores={"rrf": project_scores[self._project_key(item)]},
                metadata={
                    "document_id": item.document_id,
                    "chunk_id": item.chunk_id,
                },
            )
            for item in project_results
        )
        return EvidenceBundle(
            passages=passages,
            knowledge_results=knowledge_results,
            project_results=project_results,
            retrieval_metrics={
                "backend": "legacy_rrf",
                "queries": list(queries),
                "knowledge_candidates": sum(map(len, knowledge_runs)),
                "project_candidates": sum(map(len, project_runs)),
                "review_statuses": list(allowed_statuses),
            },
        )

    @staticmethod
    def _review_statuses(request: RetrievalRequest) -> tuple[str, ...]:
        """Keep failover evidence eligibility aligned with PostgreSQL retrieval."""

        if request.risk == "high" or request.currentness == "current":
            return ("approved",)
        return (
            "approved",
            "field_review",
            "technical_review",
            "draft",
            "ai_draft",
        )

    def _fuse_knowledge(
        self, runs: list[list[SearchResult]], limit: int
    ) -> tuple[list[SearchResult], dict[str, float]]:
        scores: dict[str, float] = {}
        items: dict[str, SearchResult] = {}
        for run in runs:
            for rank, item in enumerate(run, start=1):
                scores[item.item_id] = scores.get(item.item_id, 0.0) + 1.0 / (
                    self.rrf_k + rank
                )
                current = items.get(item.item_id)
                if current is None or item.score > current.score:
                    items[item.item_id] = item
        ordered = sorted(items.values(), key=lambda item: scores[item.item_id], reverse=True)
        return ordered[: max(1, limit)], scores

    def _fuse_projects(
        self, runs: list[list[ProjectSearchResult]], limit: int
    ) -> tuple[list[ProjectSearchResult], dict[str, float]]:
        scores: dict[str, float] = {}
        items: dict[str, ProjectSearchResult] = {}
        for run in runs:
            for rank, item in enumerate(run, start=1):
                key = self._project_key(item)
                scores[key] = scores.get(key, 0.0) + 1.0 / (self.rrf_k + rank)
                current = items.get(key)
                if current is None or item.score > current.score:
                    items[key] = item
        ordered = sorted(
            items.values(), key=lambda item: scores[self._project_key(item)], reverse=True
        )
        return ordered[: max(1, limit)], scores

    @staticmethod
    def _project_key(item: ProjectSearchResult) -> str:
        return f"{item.document_id}:{item.chunk_id}"


class PostgresGraphRetrieval(RetrievalService):
    """Versioned PostgreSQL lexical/vector/alias/graph retrieval with safe fallback."""

    def __init__(
        self,
        repository: GraphRepository,
        legacy: LegacyHybridRetrieval,
        provider: ProviderClient,
        *,
        deployment_scope: str = "pilot",
        embedding_model: str | None = None,
        embedding_dimensions: int | None = None,
        vector_approved: bool = False,
        embedding_approval_sha256: str | None = None,
        rrf_k: int = 60,
    ) -> None:
        self.repository = repository
        self.legacy = legacy
        self.provider = provider
        self.deployment_scope = deployment_scope
        self.embedding_model = embedding_model
        self.embedding_dimensions = embedding_dimensions
        self.vector_approved = bool(
            vector_approved and embedding_model and embedding_dimensions
        )
        self.embedding_approval_sha256 = embedding_approval_sha256
        self.rrf_k = max(1, int(rrf_k))
        self._embedding_cache: dict[str, tuple[float, ...]] = {}

    async def retrieve(
        self,
        request: RetrievalRequest,
        *,
        project_chunks: list[dict[str, Any]] | None = None,
    ) -> EvidenceBundle:
        try:
            release_id = await asyncio.to_thread(
                self.repository.active_release, self.deployment_scope
            )
        except (GraphRepositoryError, PsycopgError, OSError):
            bundle = await self.legacy.retrieve(
                request, project_chunks=project_chunks
            )
            bundle.warnings.append("Graph index unavailable; using local lexical index.")
            bundle.retrieval_metrics["fallback"] = "graph_unavailable"
            return bundle
        if not release_id:
            bundle = await self.legacy.retrieve(
                request, project_chunks=project_chunks
            )
            bundle.warnings.append("No active graph release; using local lexical index.")
            bundle.retrieval_metrics["fallback"] = "no_active_release"
            return bundle

        queries = tuple(dict.fromkeys((request.query, *request.queries)))[:4]
        warnings: list[str] = []
        embeddings: list[tuple[float, ...] | None] = [None] * len(queries)
        if self.vector_approved:
            try:
                embeddings = await self._embeddings(queries)
            except (httpx.HTTPError, RuntimeError, ValueError):
                warnings.append(
                    "Embedding service unavailable; lexical and graph retrieval remained active."
                )
        statuses = self._review_statuses(request)
        candidate_limit = min(50, max(request.top_k * 3, request.top_k))
        runs = list(
            await asyncio.gather(
                *(
                    asyncio.to_thread(
                        self.repository.hybrid_search,
                        release_id=release_id,
                        query=query,
                        embedding=embeddings[index],
                        embedding_model=(
                            self.embedding_model if embeddings[index] else None
                        ),
                        embedding_dimensions=(
                            self.embedding_dimensions if embeddings[index] else None
                        ),
                        top_k=candidate_limit,
                        review_statuses=statuses,
                    )
                    for index, query in enumerate(queries)
                )
            )
        )
        rows, scores = self._fuse_rows(runs)
        rows = self._language_and_geography_filter(rows, request)
        selected = rows[: max(1, request.top_k)]

        project_results: list[ProjectSearchResult] = []
        if request.actor_id and request.project_id:
            project_runs = list(
                await asyncio.gather(
                    *(
                        asyncio.to_thread(
                            self.repository.hybrid_project_search,
                            owner_user_id=request.actor_id,
                            project_id=request.project_id,
                            query=query,
                            embedding=embeddings[index],
                            embedding_model=(
                                self.embedding_model if embeddings[index] else None
                            ),
                            embedding_dimensions=(
                                self.embedding_dimensions if embeddings[index] else None
                            ),
                            top_k=min(8, candidate_limit),
                        )
                        for index, query in enumerate(queries)
                    )
                )
            )
            project_rows, _ = self._fuse_rows(project_runs, key="chunk_id")
            project_results = [
                ProjectSearchResult(
                    chunk_id=str(row["chunk_id"]),
                    document_id=str(row["document_id"]),
                    filename=str(row["filename"]),
                    text=str(row["content"]),
                    score=float(row.get("rrf_score") or row.get("score") or 0),
                )
                for row in project_rows[: min(5, request.top_k)]
            ]
        if not project_results and project_chunks:
            legacy_project = await self.legacy.retrieve(
                request, project_chunks=project_chunks
            )
            project_results = legacy_project.project_results

        entity_rows = await asyncio.to_thread(
            self.repository.resolve_entities,
            release_id=release_id,
            query=" ".join(queries),
            limit=12,
        )
        entity_ids = tuple(
            dict.fromkeys(str(row["id"]) for row in entity_rows)
        )
        paths = await asyncio.to_thread(
            self.repository.graph_paths,
            release_id=release_id,
            entity_ids=entity_ids,
            max_hops=request.graph_hops,
            review_statuses=statuses,
            limit=min(50, max(request.top_k * 3, request.top_k)),
        )
        paths = self._language_and_geography_filter(paths, request)[
            : min(50, max(request.top_k * 3, request.top_k))
        ]

        knowledge_results = [self._search_result(row) for row in selected]
        passages = [self._evidence_item(row, scores) for row in selected]
        claims = [self._graph_evidence_item(path) for path in paths]
        knowledge_results.extend(self._graph_search_result(path) for path in paths)
        passages.extend(
            EvidenceItem(
                evidence_id=f"project:{item.document_id}:{item.chunk_id}",
                source_type="project_document",
                title=item.filename,
                excerpt=item.text,
                language=None,
                review_status="user_provided",
                scores={"rrf": item.score},
                metadata={
                    "document_id": item.document_id,
                    "chunk_id": item.chunk_id,
                    "tenant_scoped": True,
                },
            )
            for item in project_results
        )
        return EvidenceBundle(
            passages=passages,
            claims=claims,
            graph_paths=paths,
            warnings=warnings,
            knowledge_results=knowledge_results,
            project_results=project_results,
            retrieval_metrics={
                "backend": "postgres_hybrid_graph",
                "release_id": release_id,
                "queries": list(queries),
                "ranking_channels": [
                    "lexical",
                    *(["vector"] if any(embeddings) else []),
                    "alias",
                    "graph",
                    *(["project"] if project_results else []),
                ],
                "vector_approved": self.vector_approved,
                "embedding_approval_sha256": self.embedding_approval_sha256,
                "graph_hops": min(2, max(1, request.graph_hops)),
                "resolved_entities": list(entity_ids),
            },
        )

    async def _embeddings(
        self, queries: tuple[str, ...]
    ) -> list[tuple[float, ...] | None]:
        results: list[tuple[float, ...] | None] = [None] * len(queries)
        missing: list[str] = []
        indexes: list[int] = []
        for index, query in enumerate(queries):
            key = hashlib.sha256(
                f"{self.embedding_model}:{self.embedding_dimensions}:{query}".encode()
            ).hexdigest()
            cached = self._embedding_cache.get(key)
            if cached is not None:
                results[index] = cached
            else:
                missing.append(query)
                indexes.append(index)
        if missing:
            response = await self.provider.embed(
                stage="retrieval_embedding",
                inputs=missing,
                model=str(self.embedding_model),
                dimensions=self.embedding_dimensions,
            )
            for index, query, embedding in zip(
                indexes, missing, response.embeddings, strict=True
            ):
                value = tuple(embedding)
                key = hashlib.sha256(
                    f"{self.embedding_model}:{self.embedding_dimensions}:{query}".encode()
                ).hexdigest()
                self._embedding_cache[key] = value
                results[index] = value
        return results

    def _fuse_rows(
        self,
        runs: list[list[dict[str, Any]]],
        *,
        key: str = "evidence_id",
    ) -> tuple[list[dict[str, Any]], dict[str, float]]:
        scores: dict[str, float] = {}
        items: dict[str, dict[str, Any]] = {}
        for run in runs:
            for rank, row in enumerate(run, start=1):
                item_key = str(row[key])
                scores[item_key] = scores.get(item_key, 0.0) + 1.0 / (
                    self.rrf_k + rank
                )
                current = items.get(item_key)
                if current is None or float(row.get("score") or 0) > float(
                    current.get("score") or 0
                ):
                    items[item_key] = dict(row)
        ordered = sorted(items.values(), key=lambda row: scores[str(row[key])], reverse=True)
        for row in ordered:
            row["rrf_score"] = scores[str(row[key])]
        return ordered, scores

    def _review_statuses(self, request: RetrievalRequest) -> tuple[str, ...]:
        if (
            self.deployment_scope == "production"
            or request.risk == "high"
            or request.currentness == "current"
        ):
            return ("approved",)
        return (
            "approved",
            "field_review",
            "technical_review",
            "draft",
            "ai_draft",
        )

    @staticmethod
    def _language_and_geography_filter(
        rows: list[dict[str, Any]], request: RetrievalRequest
    ) -> list[dict[str, Any]]:
        geography = (request.geography or "").casefold()
        eligible: list[dict[str, Any]] = []
        for row in rows:
            value = row.get("geography_json") or []
            if isinstance(value, str):
                try:
                    value = json.loads(value)
                except json.JSONDecodeError:
                    value = []
            places = (
                [str(item).casefold() for item in value]
                if isinstance(value, list)
                else []
            )
            if geography and places and not any(
                geography in place or place in geography for place in places
            ):
                continue
            eligible.append(row)
        matching = [
            row
            for row in eligible
            if str(row.get("language") or "").casefold()
            in {request.language.casefold(), request.language[:2].casefold()}
        ]
        others = [row for row in eligible if row not in matching]
        return [*matching, *others]

    @staticmethod
    def _search_result(row: dict[str, Any]) -> SearchResult:
        geography = row.get("geography_json") or []
        if isinstance(geography, str):
            geography = json.loads(geography)
        return SearchResult(
            item_id=str(row["evidence_id"]),
            title=str(row["title"]),
            text=str(row["content"]),
            language=str(row.get("language") or "unknown"),
            geography=tuple(str(item) for item in geography or []),
            topics=(),
            source_ids=(str(row["source_id"]),),
            evidence_class="versioned_graph_passage",
            risk=str(row.get("risk") or "medium"),
            status=str(row.get("review_status") or "unknown"),
            score=float(row.get("rrf_score") or row.get("score") or 0),
        )

    @staticmethod
    def _evidence_item(
        row: dict[str, Any], scores: dict[str, float]
    ) -> EvidenceItem:
        geography = row.get("geography_json") or []
        if isinstance(geography, str):
            geography = json.loads(geography)
        evidence_id = str(row["evidence_id"])
        return EvidenceItem(
            evidence_id=evidence_id,
            source_type="graph_release_passage",
            title=str(row["title"]),
            excerpt=str(row["content"]),
            language=str(row.get("language") or "unknown"),
            review_status=str(row.get("review_status") or "unknown"),
            source_ids=(str(row["source_id"]),),
            geography=tuple(str(item) for item in geography or []),
            risk=str(row.get("risk") or "medium"),
            scores={
                "rrf": scores.get(evidence_id, 0.0),
                "lexical_rank": float(row.get("lexical_rank") or 0),
                "semantic_rank": float(row.get("semantic_rank") or 0),
            },
            metadata={
                "chunk_id": row.get("chunk_id"),
                "document_id": row.get("document_id"),
                "immutable": True,
            },
        )

    @staticmethod
    def _graph_text(row: dict[str, Any]) -> str:
        subject = str(row.get("subject_label") or row["subject_entity_id"])
        predicate = str(row["predicate"]).replace("_", " ")
        target = str(
            row.get("object_label")
            or row.get("object_text")
            or row.get("object_entity_id")
            or "an unspecified target"
        )
        return f"{subject} {predicate} {target}."

    @classmethod
    def _graph_search_result(cls, row: dict[str, Any]) -> SearchResult:
        geography = row.get("geography_json") or []
        if isinstance(geography, str):
            try:
                geography = json.loads(geography)
            except json.JSONDecodeError:
                geography = []
        return SearchResult(
            item_id=f"graph:{row['id']}:{row.get('depth', 1)}",
            title="Evidence-backed knowledge graph relation",
            text=cls._graph_text(row),
            language="multilingual",
            geography=tuple(str(item) for item in geography or []),
            topics=(str(row["predicate"]),),
            source_ids=tuple(str(item) for item in row.get("source_ids") or []),
            evidence_class="graph_relation",
            risk=str(row.get("risk") or "medium"),
            status=str(row.get("review_status") or "unknown"),
            score=1.0 / max(1, int(row.get("depth") or 1)),
        )

    @classmethod
    def _graph_evidence_item(cls, row: dict[str, Any]) -> EvidenceItem:
        geography = row.get("geography_json") or []
        if isinstance(geography, str):
            try:
                geography = json.loads(geography)
            except json.JSONDecodeError:
                geography = []
        return EvidenceItem(
            evidence_id=f"graph:{row['id']}:{row.get('depth', 1)}",
            source_type="graph_relation",
            title="Evidence-backed knowledge graph relation",
            excerpt=cls._graph_text(row),
            language="multilingual",
            review_status=str(row.get("review_status") or "unknown"),
            source_ids=tuple(str(item) for item in row.get("source_ids") or []),
            geography=tuple(str(item) for item in geography or []),
            risk=str(row.get("risk") or "medium"),
            scores={"graph_depth": float(row.get("depth") or 1)},
            metadata={
                "relation_id": str(row["id"]),
                "predicate": str(row["predicate"]),
                "evidence_ids": [
                    str(item) for item in row.get("evidence_ids") or []
                ],
                "passage_ids": [
                    str(item) for item in row.get("passage_ids") or []
                ],
                "immutable": True,
            },
        )
