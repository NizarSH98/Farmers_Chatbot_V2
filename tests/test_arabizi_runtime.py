from __future__ import annotations

import asyncio

import pytest

from farmers_chatbot.arabizi import arabic_to_arabizi
from farmers_chatbot.qdrant_retrieval import QdrantGraphRetrieval
from farmers_chatbot.retrieval import RetrievalRequest

pytestmark = pytest.mark.arabic


class _EmptyRepository:
    def resolve_entities(self, **_: object) -> list[dict[str, object]]:
        return []


def test_generated_arabizi_alias_expands_to_bilingual_entity_labels() -> None:
    retrieval = object.__new__(QdrantGraphRetrieval)
    retrieval.repository = _EmptyRepository()
    potato = arabic_to_arabizi("البطاطا")
    request = RetrievalRequest(
        query=f"shu lezim a3mel lal {potato}",
        language="ar-LB-Latn",
        mode="quick",
    )

    variants = asyncio.run(retrieval._alias_query_variants(request, "release-test"))

    assert "البطاطا" in variants
    assert "potato" in variants
