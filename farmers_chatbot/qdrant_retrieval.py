"""Adaptive local Qdrant retrieval over an authoritative PostgreSQL graph."""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from dataclasses import replace
from typing import Any, Literal

import networkx as nx
from qdrant_client import AsyncQdrantClient, models
from qdrant_client.http.exceptions import ApiException

from .agrifood_ontology import ENTITIES
from .arabizi import arabic_to_arabizi
from .documents import ProjectSearchResult
from .graph_repository import GraphRepository, GraphRepositoryError
from .knowledge import SearchResult
from .qdrant_projection import (
    LocalEmbeddingService,
    ProjectionConfig,
    ProjectionError,
    QdrantProjectionRepository,
)
from .retrieval import (
    EvidenceBundle,
    EvidenceItem,
    RetrievalRequest,
    RetrievalService,
)

RetrievalRoute = Literal["vector", "contextual", "lazy_graph"]
_ROUTES = frozenset({"vector", "contextual", "lazy_graph"})


class QdrantGraphRetrieval(RetrievalService):
    """Dense/BM25 Qdrant fusion plus bounded evidence-backed graph expansion.

    PostgreSQL selects the immutable active release and remains authoritative.
    Qdrant is queried by that release's exact versioned collection name; aliases
    are never used for correctness. Any projection/vector failure falls back to
    the existing PostgreSQL lexical/graph service.
    """

    def __init__(
        self,
        repository: GraphRepository,
        projection_repository: QdrantProjectionRepository,
        fallback: RetrievalService,
        *,
        deployment_scope: str = "pilot",
        config: ProjectionConfig | None = None,
        client: AsyncQdrantClient | None = None,
        embeddings: LocalEmbeddingService | None = None,
    ) -> None:
        self.repository = repository
        self.projections = projection_repository
        self.fallback = fallback
        self.deployment_scope = deployment_scope
        self.config = config or ProjectionConfig.from_env()
        self.client = client or AsyncQdrantClient(
            url=self.config.url,
            api_key=self.config.api_key,
            timeout=self.config.timeout_seconds,
        )
        self.embeddings = embeddings or LocalEmbeddingService(self.config)

    async def close(self) -> None:
        await self.client.close()

    @staticmethod
    def route(request: RetrievalRequest) -> RetrievalRoute:
        override = request.route_override
        if override:
            if override not in _ROUTES:
                raise ValueError(f"unsupported retrieval route: {override}")
            return override  # type: ignore[return-value]
        lowered = request.query.casefold()
        multi_factor = any(
            marker in lowered
            for marker in (
                "because",
                "compare",
                "سبب",
                "لماذا",
                "قارن",
                "impact",
                "trade-off",
                "then",
            )
        )
        if request.mode == "deep" or request.graph_hops >= 2 or multi_factor:
            return "lazy_graph"
        if request.mode == "standard" or request.risk in {"high", "critical"}:
            return "contextual"
        return "vector"

    @staticmethod
    def _likely_arabizi(request: RetrievalRequest) -> bool:
        text = request.query.casefold()
        has_latin = any(character.isascii() and character.isalpha() for character in text)
        has_arabizi_digit = any(character in "2378" for character in text)
        return request.language.lower().startswith("ar") and has_latin and (
            has_arabizi_digit
            or any(token in text.split() for token in ("shu", "kif", "iza", "fine", "lezim"))
        )

    async def _alias_query_variants(
        self, request: RetrievalRequest, release_id: str
    ) -> tuple[str, ...]:
        if not self._likely_arabizi(request):
            return ()
        entities = await asyncio.to_thread(
            self.repository.resolve_entities,
            release_id=release_id,
            query=request.query,
            limit=8,
        )
        variants: list[str] = []
        for entity in entities:
            for key in ("label_ar", "label_en"):
                value = str(entity.get(key) or "").strip()
                if value and value not in variants:
                    variants.append(value)

        normalized_query = " ".join(request.query.casefold().split())
        for entity in ENTITIES:
            generated_alias = arabic_to_arabizi(entity.label_ar)
            if len(generated_alias) >= 3 and generated_alias in normalized_query:
                for value in (entity.label_ar, entity.label_en):
                    if value and value not in variants:
                        variants.append(value)
        return tuple(variants[:6])

    async def retrieve(
        self,
        request: RetrievalRequest,
        *,
        project_chunks: list[dict[str, Any]] | None = None,
    ) -> EvidenceBundle:
        route = self.route(request)
        effective_request = request
        try:
            release_id = request.release_pin or await asyncio.to_thread(
                self.repository.active_release, self.deployment_scope
            )
            if not release_id:
                raise ProjectionError("no active PostgreSQL release")
            projection = await asyncio.to_thread(
                self.projections.projection, release_id
            )
            if not projection or projection.get("state") != "ready":
                raise ProjectionError("active release has no ready Qdrant projection")
            alias_variants = await self._alias_query_variants(request, release_id)
            if alias_variants:
                effective_request = replace(
                    request,
                    queries=tuple(dict.fromkeys((*request.queries, *alias_variants))),
                    language="ar",
                )
            passages, claims = await self._query_evidence(
                effective_request, release_id, projection, route
            )
            paths = await self._query_graph(effective_request, release_id, projection, route)
            project_results = await self._project_results(
                effective_request, project_chunks=project_chunks
            )
        except (
            ApiException,
            OSError,
            TimeoutError,
            ProjectionError,
            GraphRepositoryError,
        ) as exc:
            bundle = await self.fallback.retrieve(
                effective_request, project_chunks=project_chunks
            )
            bundle.warnings.append(
                "Qdrant projection unavailable; PostgreSQL/lexical retrieval remained active."
            )
            bundle.retrieval_metrics.update(
                {
                    "fallback": "qdrant_unavailable",
                    "fallback_error": type(exc).__name__,
                    "requested_route": route,
                    "projection_status": "unavailable",
                }
            )
            bundle.projection_status = "unavailable"
            return bundle

        graph_items = [self._graph_evidence_item(path) for path in paths]
        project_items = [self._project_evidence_item(item) for item in project_results]
        knowledge_results = [
            self._search_result(item) for item in [*passages, *claims, *graph_items]
        ]
        channels = ["dense", "bm25", "rrf", "qdrant_formula"]
        if route != "vector":
            channels.extend(["entity_alias", "graph"])
        if route == "lazy_graph":
            channels.extend(["personalized_pagerank", "path_pruning"])
        if project_results:
            channels.append("tenant_project")
        return EvidenceBundle(
            passages=[*passages, *project_items],
            claims=[*claims, *graph_items],
            graph_paths=paths,
            knowledge_results=knowledge_results,
            project_results=project_results,
            release_id=release_id,
            retrieval_route=route,
            ranking_channels=channels,
            projection_status="ready",
            retrieval_metrics={
                "backend": "qdrant_lazy_graphrag",
                "release_id": release_id,
                "retrieval_route": route,
                "ranking_channels": channels,
                "projection_status": "ready",
                "graph_hops": 0 if route == "vector" else (2 if route == "lazy_graph" else 1),
                "evidence_count": len(passages) + len(claims),
                "graph_path_count": len(paths),
            },
        )

    def _statuses(self, request: RetrievalRequest) -> list[str]:
        if self.deployment_scope == "production" or request.risk in {
            "high",
            "critical",
        } or request.currentness == "current":
            return ["approved"]
        return ["approved", "field_review", "technical_review", "draft", "ai_draft"]

    async def _vectors(
        self, query: str, language: str
    ) -> tuple[list[float], models.SparseVector]:
        dense, sparse = await asyncio.gather(
            asyncio.to_thread(self.embeddings.dense, [query], query=True),
            asyncio.to_thread(self.embeddings.sparse, [query], [language]),
        )
        return dense[0], sparse[0]

    async def _hybrid_points(
        self,
        *,
        collection: str,
        query: str,
        language: str,
        limit: int,
        release_id: str,
        statuses: Sequence[str] | None = None,
    ) -> list[Any]:
        dense, sparse = await self._vectors(query, language)
        must: list[Any] = [
            models.FieldCondition(
                key="release_id", match=models.MatchValue(value=release_id)
            )
        ]
        if statuses:
            must.append(
                models.FieldCondition(
                    key="review_status", match=models.MatchAny(any=list(statuses))
                )
            )
        query_filter = models.Filter(must=must)
        candidate_limit = min(100, max(limit * 4, 20))
        prefetch = models.Prefetch(
            prefetch=[
                models.Prefetch(
                    query=dense,
                    using="dense",
                    filter=query_filter,
                    limit=candidate_limit,
                ),
                models.Prefetch(
                    query=sparse,
                    using="bm25",
                    filter=query_filter,
                    limit=candidate_limit,
                ),
            ],
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            limit=candidate_limit,
        )
        formula = models.FormulaQuery(
            formula=models.SumExpression(
                sum=[
                    "$score",
                    models.MultExpression(mult=[0.01, "evidence_count"]),
                    models.MultExpression(mult=[0.05, "pagerank_global"]),
                ]
            ),
            defaults={"evidence_count": 0, "pagerank_global": 0.0},
        )
        response = await self.client.query_points(
            collection_name=collection,
            prefetch=prefetch,
            query=formula,
            limit=max(1, limit),
            with_payload=True,
        )
        return list(response.points)

    async def _arabizi_phrase_points(
        self,
        *,
        collection: str,
        query: str,
        release_id: str,
        statuses: Sequence[str],
        limit: int,
    ) -> list[Any]:
        tokens = query.casefold().split()
        if len(tokens) < 5:
            return []
        windows = [
            " ".join(tokens[index : index + 5])
            for index in range(min(len(tokens) - 4, 16))
        ]
        must: list[Any] = [
            models.FieldCondition(
                key="release_id", match=models.MatchValue(value=release_id)
            ),
            models.FieldCondition(
                key="review_status", match=models.MatchAny(any=list(statuses))
            ),
        ]
        points, _ = await self.client.scroll(
            collection_name=collection,
            scroll_filter=models.Filter(
                must=must,
                should=[
                    models.FieldCondition(
                        key="content_arabizi", match=models.MatchText(text=window)
                    )
                    for window in windows
                ],
            ),
            limit=max(1, limit),
            with_payload=True,
            with_vectors=False,
        )
        return list(points)

    async def _query_evidence(
        self,
        request: RetrievalRequest,
        release_id: str,
        projection: dict[str, Any],
        route: RetrievalRoute,
    ) -> tuple[list[EvidenceItem], list[EvidenceItem]]:
        queries = tuple(dict.fromkeys((request.query, *request.queries)))[:4]
        if self._likely_arabizi(request):
            queries = (request.query,)
        per_query = min(40, max(request.top_k * 3, request.top_k))
        runs = await asyncio.gather(
            *(
                self._hybrid_points(
                    collection=str(projection["evidence_collection"]),
                    query=query,
                    language=request.language,
                    limit=per_query,
                    release_id=release_id,
                    statuses=self._statuses(request),
                )
                for query in queries
            )
        )
        exact_points = (
            await self._arabizi_phrase_points(
                collection=str(projection["evidence_collection"]),
                query=request.query,
                release_id=release_id,
                statuses=self._statuses(request),
                limit=request.top_k * 2,
            )
            if self._likely_arabizi(request)
            else []
        )
        scores: dict[str, float] = {}
        points: dict[str, Any] = {}
        for run in runs:
            for rank, point in enumerate(run, start=1):
                point_id = str(point.id)
                scores[point_id] = scores.get(point_id, 0.0) + 1.0 / (60 + rank)
                if point_id not in points or self._point_score(point) > self._point_score(points[point_id]):
                    points[point_id] = point
        for rank, point in enumerate(exact_points, start=1):
            point_id = str(point.id)
            scores[point_id] = scores.get(point_id, 0.0) + 1.0 / (10 + rank)
            points.setdefault(point_id, point)
        ordered = sorted(points.values(), key=lambda point: scores[str(point.id)], reverse=True)
        selected = self._diversify(ordered, request.top_k)
        passages: list[EvidenceItem] = []
        claims: list[EvidenceItem] = []
        for point in selected:
            payload = dict(point.payload or {})
            item = self._point_evidence(point, payload, scores[str(point.id)])
            (claims if payload.get("record_type") == "claim" else passages).append(item)
        return passages, claims

    @staticmethod
    def _diversify(points: list[Any], limit: int) -> list[Any]:
        selected: list[Any] = []
        per_document: dict[str, int] = {}
        for point in points:
            payload = point.payload or {}
            document = str(payload.get("document_id") or payload.get("record_id") or point.id)
            if per_document.get(document, 0) >= 2:
                continue
            selected.append(point)
            per_document[document] = per_document.get(document, 0) + 1
            if len(selected) >= max(1, limit):
                break
        return selected

    async def _query_graph(
        self,
        request: RetrievalRequest,
        release_id: str,
        projection: dict[str, Any],
        route: RetrievalRoute,
    ) -> list[dict[str, Any]]:
        if route == "vector":
            return []
        points = await self._hybrid_points(
            collection=str(projection["entity_collection"]),
            query=" ".join(tuple(dict.fromkeys((request.query, *request.queries)))[:4]),
            language=request.language,
            limit=12,
            release_id=release_id,
        )
        direct_entities = await asyncio.to_thread(
            self.repository.resolve_entities,
            release_id=release_id,
            query=request.query,
            limit=30,
        )
        direct_entity_ids = tuple(
            dict.fromkeys(str(entity["id"]) for entity in direct_entities)
        )
        entity_ids = tuple(
            dict.fromkeys(
                (
                    *direct_entity_ids,
                    *(
                        str((point.payload or {}).get("record_id"))
                        for point in points
                        if (point.payload or {}).get("record_id")
                    ),
                )
            )
        )
        if not entity_ids:
            return []
        paths = await asyncio.to_thread(
            self.repository.graph_paths,
            release_id=release_id,
            entity_ids=entity_ids,
            max_hops=2 if route == "lazy_graph" else 1,
            review_statuses=tuple(self._statuses(request)),
            limit=min(100, max(request.top_k * 10, 40)),
        )
        if route == "lazy_graph":
            paths = self._personalized_pagerank(paths, entity_ids)
        paths = self._rank_graph_paths(paths, direct_entity_ids, request.query)
        return paths[: min(30, max(request.top_k * 3, request.top_k))]

    @staticmethod
    def _rank_graph_paths(
        paths: list[dict[str, Any]], direct_seeds: Sequence[str], query: str
    ) -> list[dict[str, Any]]:
        seed_set = set(direct_seeds)
        normalized_query = " ".join(query.casefold().replace("_", " ").split())

        def score(path: dict[str, Any]) -> tuple[float, int, str]:
            subject = str(path.get("subject_entity_id") or "")
            target = str(path.get("object_entity_id") or "")
            predicate = str(path.get("predicate") or "").casefold().replace("_", " ")
            endpoint_matches = int(subject in seed_set) + int(target in seed_set)
            predicate_match = bool(predicate and predicate in normalized_query)
            relevance = (
                endpoint_matches * 10.0
                + (8.0 if predicate_match else 0.0)
                + float(path.get("personalized_pagerank") or 0.0)
            )
            path["query_path_score"] = relevance
            return (-relevance, int(path.get("depth") or 1), str(path.get("id") or ""))

        return sorted((dict(path) for path in paths), key=score)

    @staticmethod
    def _personalized_pagerank(
        paths: list[dict[str, Any]], seeds: Sequence[str]
    ) -> list[dict[str, Any]]:
        graph = nx.DiGraph()
        for path in paths:
            subject = str(path.get("subject_entity_id") or "")
            target = str(path.get("object_entity_id") or "")
            if subject and target:
                graph.add_edge(subject, target)
        if not graph:
            return paths
        personalization = {node: (1.0 if node in seeds else 0.0) for node in graph}
        if not any(personalization.values()):
            return paths
        ranks = nx.pagerank(graph, personalization=personalization)
        enriched = []
        for path in paths:
            target = str(path.get("object_entity_id") or "")
            value = dict(path)
            value["personalized_pagerank"] = float(ranks.get(target, 0.0))
            enriched.append(value)
        return sorted(
            enriched,
            key=lambda item: (
                -float(item.get("personalized_pagerank") or 0),
                int(item.get("depth") or 1),
                str(item.get("id") or ""),
            ),
        )

    async def _project_results(
        self,
        request: RetrievalRequest,
        *,
        project_chunks: list[dict[str, Any]] | None,
    ) -> list[ProjectSearchResult]:
        if not (request.project_id or project_chunks):
            return []
        bundle = await self.fallback.retrieve(request, project_chunks=project_chunks)
        return bundle.project_results[: min(5, request.top_k)]

    @staticmethod
    def _point_score(point: Any) -> float:
        return float(getattr(point, "score", None) or 0.0)

    @staticmethod
    def _point_evidence(point: Any, payload: dict[str, Any], rrf: float) -> EvidenceItem:
        record_type = str(payload.get("record_type") or "chunk")
        record_id = str(payload.get("record_id") or point.id)
        return EvidenceItem(
            evidence_id=f"qdrant:{record_type}:{record_id}",
            source_type="qdrant_claim" if record_type == "claim" else "qdrant_passage",
            title=str(payload.get("section_path") or ("Knowledge claim" if record_type == "claim" else "Knowledge passage")),
            excerpt=str(payload.get("content") or ""),
            language=str(payload.get("language") or "unknown"),
            review_status=str(payload.get("review_status") or "unknown"),
            source_ids=tuple(str(value) for value in payload.get("source_ids") or []),
            geography=tuple(str(value) for value in payload.get("geography") or []),
            risk=str(payload.get("risk") or "medium"),
            scores={"qdrant": QdrantGraphRetrieval._point_score(point), "rrf": rrf},
            metadata={
                "point_uuid": str(point.id),
                "record_id": record_id,
                "document_id": payload.get("document_id"),
                "chunk_hash": payload.get("chunk_hash"),
                "immutable": True,
            },
        )

    @staticmethod
    def _graph_evidence_item(path: dict[str, Any]) -> EvidenceItem:
        subject = str(path.get("subject_label") or path.get("subject_entity_id") or "")
        predicate = str(path.get("predicate") or "related_to").replace("_", " ")
        target = str(path.get("object_label") or path.get("object_text") or path.get("object_entity_id") or "")
        return EvidenceItem(
            evidence_id=f"graph:{path.get('id')}:{path.get('depth', 1)}",
            source_type="graph_relation",
            title="Evidence-backed knowledge graph relation",
            excerpt=f"{subject} {predicate} {target}.",
            language="multilingual",
            review_status=str(path.get("review_status") or "unknown"),
            source_ids=tuple(str(value) for value in path.get("source_ids") or []),
            geography=tuple(str(value) for value in path.get("geography_json") or []),
            risk=str(path.get("risk") or "medium"),
            scores={
                "graph_depth": float(path.get("depth") or 1),
                "personalized_pagerank": float(path.get("personalized_pagerank") or 0),
            },
            metadata={"relation_id": path.get("id"), "immutable": True},
        )

    @staticmethod
    def _project_evidence_item(item: ProjectSearchResult) -> EvidenceItem:
        return EvidenceItem(
            evidence_id=f"project:{item.document_id}:{item.chunk_id}",
            source_type="project_document",
            title=item.filename,
            excerpt=item.text,
            language=None,
            review_status="user_provided",
            scores={"score": item.score},
            metadata={"document_id": item.document_id, "chunk_id": item.chunk_id, "tenant_scoped": True},
        )

    @staticmethod
    def _search_result(item: EvidenceItem) -> SearchResult:
        return SearchResult(
            item_id=item.evidence_id,
            title=item.title,
            text=item.excerpt,
            language=item.language or "unknown",
            geography=item.geography,
            topics=(),
            source_ids=item.source_ids,
            evidence_class=item.source_type,
            risk=item.risk,
            status=item.review_status,
            score=max(item.scores.values(), default=0.0),
        )
