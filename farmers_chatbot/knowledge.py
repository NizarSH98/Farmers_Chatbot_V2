"""Shared retrieval result contract.

This module previously held a TF-IDF index over the legacy `guide.json` corpus.
That corpus was superseded by the versioned v0.3 release in PostgreSQL/Qdrant,
and serving it alongside the release let unapproved draft content reach answers.
Only the result shape shared by retrieval and the tool layer survives here; see
`release_knowledge.ReleaseKnowledgeGateway` for release-scoped lookup.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SearchResult:
    item_id: str
    title: str
    text: str
    language: str
    geography: tuple[str, ...]
    topics: tuple[str, ...]
    source_ids: tuple[str, ...]
    evidence_class: str
    risk: str
    status: str
    score: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "title": self.title,
            "text": self.text,
            "language": self.language,
            "geography": list(self.geography),
            "topics": list(self.topics),
            "source_ids": list(self.source_ids),
            "evidence_class": self.evidence_class,
            "risk": self.risk,
            "status": self.status,
            "score": self.score,
        }
