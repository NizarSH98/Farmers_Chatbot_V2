"""Structured bilingual knowledge loading and retrieval."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion
from sklearn.preprocessing import normalize


@dataclass(frozen=True)
class KnowledgeDocument:
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


class KnowledgeIndex:
    """Hybrid word/character TF-IDF index over reviewed bilingual items."""

    def __init__(
        self,
        documents: list[KnowledgeDocument],
        sources: dict[str, dict[str, Any]],
    ) -> None:
        if not documents:
            raise ValueError("Knowledge index requires at least one document")
        self.documents = documents
        self.sources = sources
        self.vectorizer = FeatureUnion(
            [
                (
                    "words",
                    TfidfVectorizer(
                        ngram_range=(1, 2),
                        sublinear_tf=True,
                        min_df=1,
                        token_pattern=r"(?u)\b\w[\w'-]+\b",
                    ),
                ),
                (
                    "characters",
                    TfidfVectorizer(
                        analyzer="char_wb",
                        ngram_range=(3, 5),
                        sublinear_tf=True,
                        min_df=1,
                        max_features=30000,
                    ),
                ),
            ]
        )
        texts = [self._index_text(document) for document in documents]
        self.vectors = normalize(self.vectorizer.fit_transform(texts))

    @staticmethod
    def _index_text(document: KnowledgeDocument) -> str:
        metadata = " ".join(
            [document.title, *document.geography, *document.topics, document.item_id]
        )
        return f"{metadata} {metadata} {document.text}"

    @classmethod
    def from_directory(
        cls,
        directory: str | Path = "knowledge_base",
        allowed_statuses: Iterable[str] | None = None,
    ) -> KnowledgeIndex:
        directory = Path(directory)
        with (directory / "guide.json").open("r", encoding="utf-8") as handle:
            guide = json.load(handle)
        with (directory / "sources.json").open("r", encoding="utf-8") as handle:
            source_items = json.load(handle)

        allowed = set(
            allowed_statuses
            or {"draft", "technical_review", "field_review", "approved"}
        )
        documents: list[KnowledgeDocument] = []
        for item in guide["items"]:
            if item["status"] not in allowed:
                continue
            common = {
                "item_id": item["id"],
                "geography": tuple(item.get("geography", [])),
                "topics": tuple(item.get("topics", [])),
                "source_ids": tuple(item.get("source_ids", [])),
                "evidence_class": item.get("evidence_class", "D"),
                "risk": item.get("risk", "medium"),
                "status": item["status"],
            }
            documents.append(
                KnowledgeDocument(
                    title=item["title_en"],
                    text=item["text_en"],
                    language="english",
                    **common,
                )
            )
            documents.append(
                KnowledgeDocument(
                    title=item["title_ar"],
                    text=item["text_ar"],
                    language="arabic",
                    **common,
                )
            )
        return cls(documents, {source["id"]: source for source in source_items})

    def search(
        self,
        query: str,
        *,
        language: str | None = None,
        top_k: int = 6,
        min_score: float = 0.01,
    ) -> list[SearchResult]:
        if not query or not query.strip():
            return []
        query_vector = normalize(self.vectorizer.transform([query]))
        scores = (query_vector @ self.vectors.T).toarray().ravel()
        if language:
            for index, document in enumerate(self.documents):
                if document.language != language:
                    scores[index] *= 0.55

        ranked = np.argsort(scores)[::-1]
        results: list[SearchResult] = []
        seen: set[str] = set()
        for index in ranked:
            document = self.documents[int(index)]
            score = float(scores[int(index)])
            if score < min_score:
                break
            if document.item_id in seen:
                continue
            seen.add(document.item_id)
            results.append(
                SearchResult(
                    score=score,
                    **document.__dict__,
                )
            )
            if len(results) >= max(1, min(top_k, 15)):
                break
        return results

    def get_item(self, item_id: str, language: str = "english") -> SearchResult | None:
        for document in self.documents:
            if document.item_id == item_id and document.language == language:
                return SearchResult(score=1.0, **document.__dict__)
        return None

    def get_source(self, source_id: str) -> dict[str, Any] | None:
        return self.sources.get(source_id)
