"""Release-backed knowledge lookup for the bounded tool layer.

The model-facing `search_knowledge` and `get_source` tools must read the same
immutable, activated release the retrieval pipeline reads. They previously read
a separate legacy TF-IDF corpus, which let unapproved draft content reach an
answer and be cited. This gateway is the single release-scoped replacement.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .graph_repository import GraphRepository
from .knowledge import SearchResult

DEFAULT_REVIEW_STATUSES: tuple[str, ...] = ("approved",)

# The release stores BCP-47-style codes; callers use detect_language() names.
_LANGUAGE_CODES = {"english": "en", "arabic": "ar"}

# Question scaffolding only. Domain words must never be dropped.
_STOPWORDS = frozenset(
    {
        "and", "are", "can", "did", "does", "for", "from", "has", "have", "how",
        "should", "that", "the", "their", "them", "there", "these", "this",
        "was", "were", "what", "when", "where", "which", "who", "why", "will",
        "with", "you", "your", "about", "into", "than", "then", "they",
        "في", "من", "على", "الى", "إلى", "عن", "مع", "هل", "ما", "ماذا",
        "متى", "اين", "أين", "كيف", "لماذا", "التي", "الذي", "هذا", "هذه",
    }
)


class ReleaseUnavailable(RuntimeError):
    """Raised when no activated knowledge release can serve a lookup."""


@dataclass(frozen=True)
class KnowledgeSearch:
    """Results plus how strictly they matched, so loose hits stay labelled."""

    results: list[SearchResult]
    # "exact": every content term matched. "broadened": any term matched, so
    # relevance is weaker and the caller must not treat hits as confirmation.
    match: str = "exact"


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
    ) -> KnowledgeSearch:
        """Lexically search the active release. No vector is supplied here."""

        release_id = self.active_release_id()
        limit = max(1, min(int(top_k), 10))
        # Over-fetch so language preference does not starve the result set.
        fetch = limit * 3
        rows = self.repository.hybrid_search(
            release_id=release_id,
            query=query,
            embedding=None,
            embedding_model=None,
            embedding_dimensions=None,
            top_k=fetch,
            review_statuses=self.review_statuses,
        )
        match = "exact"
        if not rows:
            # websearch_to_tsquery ANDs bare terms, so a natural-language
            # question rarely has a chunk containing every word. The model calls
            # this tool with questions, not keywords, so widen to OR before
            # reporting that the release has nothing.
            broadened = self._or_query(query)
            if broadened:
                match = "broadened"
                rows = self.repository.hybrid_search(
                    release_id=release_id,
                    query=broadened,
                    embedding=None,
                    embedding_model=None,
                    embedding_dimensions=None,
                    top_k=fetch,
                    review_statuses=self.review_statuses,
                )
        code = _LANGUAGE_CODES.get(language, language)
        preferred = [row for row in rows if (row.get("language") or "") == code]
        selected = preferred or rows
        return KnowledgeSearch(
            results=[self._search_result(row) for row in selected[:limit]],
            match=match if selected else "exact",
        )

    @staticmethod
    def _or_query(query: str) -> str:
        """Rewrite a natural-language question as an OR of its content terms."""

        terms = [
            term
            for term in re.findall(r"[^\W\d_]{3,}", query, flags=re.UNICODE)
            if term.casefold() not in _STOPWORDS
        ]
        # A single term already behaves as OR; rewriting adds nothing.
        return " OR ".join(dict.fromkeys(terms)) if len(terms) > 1 else ""

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
