"""Release-backed knowledge lookup for the bounded tool layer.

The model-facing `search_knowledge` and `get_source` tools must read the same
immutable, activated release the retrieval pipeline reads. They previously read
a separate legacy TF-IDF corpus, which let unapproved draft content reach an
answer and be cited. This gateway is the single release-scoped replacement.
"""

from __future__ import annotations

from typing import Any

from .graph_repository import GraphRepository
from .knowledge import SearchResult

DEFAULT_REVIEW_STATUSES: tuple[str, ...] = ("approved",)


class ReleaseUnavailable(RuntimeError):
    """Raised when no activated knowledge release can serve a lookup."""


class ReleaseKnowledgeGateway:
    """Synchronous, release-pinned knowledge access for `ToolRegistry`."""

    def __init__(
        self,
        repository: GraphRepository,
        *,
        deployment_scope: str = "pilot",
        review_statuses: tuple[str, ...] = DEFAULT_REVIEW_STATUSES,
    ) -> None:
        self.repository = repository
        self.deployment_scope = deployment_scope
        self.review_statuses = tuple(review_statuses) or DEFAULT_REVIEW_STATUSES

    def active_release_id(self) -> str:
        release_id = self.repository.active_release(self.deployment_scope)
        if not release_id:
            raise ReleaseUnavailable(
                "No activated knowledge release is available for scope "
                f"{self.deployment_scope!r}"
            )
        return release_id

    def search(
        self,
        query: str,
        *,
        language: str,
        top_k: int = 5,
    ) -> list[SearchResult]:
        """Lexically search the active release. No vector is supplied here."""

        rows = self.repository.hybrid_search(
            release_id=self.active_release_id(),
            query=query,
            embedding=None,
            embedding_model=None,
            embedding_dimensions=None,
            # Over-fetch so language preference does not starve the result set.
            top_k=max(1, min(int(top_k), 10)) * 3,
            review_statuses=self.review_statuses,
        )
        preferred = [row for row in rows if (row.get("language") or "") == language]
        selected = preferred or rows
        limit = max(1, min(int(top_k), 10))
        return [self._search_result(row) for row in selected[:limit]]

    def get_source(self, source_id: str) -> dict[str, Any] | None:
        return self.repository.source_record(
            release_id=self.active_release_id(),
            source_id=source_id,
        )

    @staticmethod
    def _search_result(row: dict[str, Any]) -> SearchResult:
        geography = row.get("geography_json") or []
        if not isinstance(geography, list):
            geography = []
        source_id = row.get("source_id")
        return SearchResult(
            item_id=str(row.get("chunk_id") or row.get("evidence_id") or ""),
            title=str(row.get("title") or ""),
            text=str(row.get("content") or ""),
            language=str(row.get("language") or ""),
            geography=tuple(str(item) for item in geography),
            topics=(),
            source_ids=(str(source_id),) if source_id else (),
            evidence_class=str(row.get("evidence_class") or "release"),
            risk=str(row.get("risk") or "medium"),
            status=str(row.get("review_status") or ""),
            score=float(row.get("score") or 0.0),
        )
