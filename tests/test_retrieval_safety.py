"""Evidence-eligibility regressions shared by primary and fallback retrieval."""

from __future__ import annotations

import pytest

from farmers_chatbot.knowledge import KnowledgeDocument, KnowledgeIndex
from farmers_chatbot.retrieval import (
    LegacyHybridRetrieval,
    PostgresGraphRetrieval,
    RetrievalRequest,
)


def _index() -> KnowledgeIndex:
    common = {
        "title": "Tomato pest control",
        "text": "Inspect tomato plants before selecting pest controls.",
        "language": "english",
        "geography": ("Lebanon",),
        "topics": ("tomato", "pest"),
        "source_ids": ("source",),
        "evidence_class": "guidance",
        "risk": "high",
    }
    return KnowledgeIndex(
        [
            KnowledgeDocument(item_id="draft", status="ai_draft", **common),
            KnowledgeDocument(item_id="approved", status="approved", **common),
        ],
        {},
    )


def _request(*, risk: str = "medium", currentness: str = "stable") -> RetrievalRequest:
    return RetrievalRequest(
        query="tomato pest control",
        language="english",
        mode="standard",
        risk=risk,
        currentness=currentness,
        top_k=5,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("risk", "currentness"),
    [("high", "stable"), ("medium", "current")],
)
async def test_legacy_failover_excludes_unapproved_evidence(
    risk: str, currentness: str
) -> None:
    result = await LegacyHybridRetrieval(_index()).retrieve(
        _request(risk=risk, currentness=currentness)
    )

    assert [item.item_id for item in result.knowledge_results] == ["approved"]
    assert {item.review_status for item in result.passages} == {"approved"}
    assert result.retrieval_metrics["review_statuses"] == ["approved"]


@pytest.mark.asyncio
async def test_legacy_pilot_still_exposes_labeled_drafts_for_stable_guidance() -> None:
    result = await LegacyHybridRetrieval(_index()).retrieve(_request())

    assert {item.item_id for item in result.knowledge_results} == {
        "approved",
        "draft",
    }
    assert {item.review_status for item in result.passages} == {
        "approved",
        "ai_draft",
    }


@pytest.mark.parametrize(
    ("risk", "currentness"),
    [("high", "stable"), ("medium", "current")],
)
def test_postgres_review_filter_matches_failover(
    risk: str, currentness: str
) -> None:
    retrieval = object.__new__(PostgresGraphRetrieval)
    retrieval.deployment_scope = "pilot"

    assert retrieval._review_statuses(
        _request(risk=risk, currentness=currentness)
    ) == ("approved",)
