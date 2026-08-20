"""Evidence-eligibility regressions shared by primary and fallback retrieval."""

from __future__ import annotations

import pytest

from farmers_chatbot.retrieval import (
    PostgresGraphRetrieval,
    ProjectOnlyFallbackRetrieval,
    RetrievalRequest,
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
async def test_terminal_fallback_serves_no_reviewed_knowledge() -> None:
    """The fallback must never substitute a superseded local corpus."""

    result = await ProjectOnlyFallbackRetrieval().retrieve(_request())

    assert result.knowledge_results == []
    assert result.passages == []
    assert result.retrieval_metrics["backend"] == "project_only_fallback"
    assert result.retrieval_metrics["knowledge_candidates"] == 0
    assert result.warnings and "unavailable" in result.warnings[0]


@pytest.mark.asyncio
async def test_terminal_fallback_still_serves_tenant_project_documents() -> None:
    chunks = [
        {
            "id": "chunk-1",
            "document_id": "doc-1",
            "filename": "soil-report.pdf",
            "text_content": "Tomato pest control notes for the Akkar plot.",
        }
    ]
    result = await ProjectOnlyFallbackRetrieval().retrieve(
        _request(), project_chunks=chunks
    )

    assert [item.source_type for item in result.passages] == ["project_document"]
    assert {item.review_status for item in result.passages} == {"user_provided"}
    assert result.knowledge_results == []


@pytest.mark.parametrize(
    ("risk", "currentness"),
    [("high", "stable"), ("medium", "current")],
)
def test_postgres_review_filter_restricts_to_approved(
    risk: str, currentness: str
) -> None:
    retrieval = object.__new__(PostgresGraphRetrieval)
    retrieval.deployment_scope = "pilot"

    assert retrieval._review_statuses(
        _request(risk=risk, currentness=currentness)
    ) == ("approved",)
