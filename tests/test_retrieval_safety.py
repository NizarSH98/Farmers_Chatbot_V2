"""Evidence-eligibility regressions shared by primary and fallback retrieval."""

from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from farmers_chatbot.assistant_contracts import TurnCommand
from farmers_chatbot.assistant_pipeline import AssistantEngine
from farmers_chatbot.qdrant_retrieval import QdrantGraphRetrieval
from farmers_chatbot.release_knowledge import (
    ReleaseKnowledgeGateway,
    ReleaseUnavailable,
)
from farmers_chatbot.retrieval import (
    EvidenceBundle,
    PostgresGraphRetrieval,
    ProjectOnlyFallbackRetrieval,
    RetrievalRequest,
)
from farmers_chatbot.tools import ToolRegistry


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


@pytest.mark.parametrize("scope", ["pilot", "production", "unknown"])
@pytest.mark.parametrize("risk", ["low", "medium", "high", "critical"])
def test_public_review_policy_is_identical_across_all_paths(scope, risk):
    request = _request(risk=risk)
    postgres = object.__new__(PostgresGraphRetrieval)
    qdrant = object.__new__(QdrantGraphRetrieval)
    postgres.deployment_scope = qdrant.deployment_scope = scope
    gateway = ReleaseKnowledgeGateway(
        Mock(), deployment_scope=scope, review_statuses=("approved", "draft", "ai_draft")
    )
    assert postgres._review_statuses(request) == ("approved",)
    assert qdrant._statuses(request) == ["approved"]
    assert gateway.review_statuses == ("approved",)


@pytest.mark.parametrize("scope", ["development", "test"])
@pytest.mark.parametrize("risk,currentness", [("high", "stable"), ("critical", "stable"), ("medium", "current")])
def test_internal_preview_cannot_widen_sensitive_turns(scope, risk, currentness):
    gateway = ReleaseKnowledgeGateway(
        Mock(), deployment_scope=scope, review_statuses=("approved", "draft")
    )
    assert gateway.review_statuses == ("approved", "draft")
    assert gateway.for_release("old", risk=risk, currentness=currentness).review_statuses == ("approved",)
    for implementation in (PostgresGraphRetrieval, QdrantGraphRetrieval):
        retrieval = object.__new__(implementation)
        retrieval.deployment_scope = scope
        statuses = retrieval._review_statuses if implementation is PostgresGraphRetrieval else retrieval._statuses
        assert tuple(statuses(_request(risk=risk, currentness=currentness))) == ("approved",)


def _repository():
    repository = Mock()
    repository.active_release.return_value = "old"
    repository.hybrid_search.return_value = []
    repository.resolve_entities.return_value = []
    repository.graph_paths.return_value = []
    repository.source_record.side_effect = lambda **kwargs: kwargs
    return repository


@pytest.mark.asyncio
async def test_postgres_honors_explicit_release_pin():
    repository = _repository()
    repository.active_release.return_value = "new"
    retrieval = PostgresGraphRetrieval(repository, ProjectOnlyFallbackRetrieval(), Mock())
    bundle = await retrieval.retrieve(replace(_request(), release_pin="old"))
    repository.active_release.assert_not_called()
    assert bundle.release_id == "old"
    for method in (repository.hybrid_search, repository.resolve_entities, repository.graph_paths):
        assert method.call_args.kwargs["release_id"] == "old"


@pytest.mark.asyncio
async def test_qdrant_failure_pins_postgres_fallback_during_activation():
    repository = _repository()
    projections = Mock()
    def activate_new_release(_release_id):
        repository.active_release.return_value = "new"
    projections.projection.side_effect = activate_new_release
    retrieval = object.__new__(QdrantGraphRetrieval)
    retrieval.repository = repository
    retrieval.projections = projections
    retrieval.deployment_scope = "pilot"
    retrieval.fallback = PostgresGraphRetrieval(repository, ProjectOnlyFallbackRetrieval(), Mock())
    bundle = await retrieval.retrieve(_request())
    assert repository.active_release.return_value == "new"
    assert repository.active_release.call_count == 1
    assert bundle.release_id == "old"
    assert repository.hybrid_search.call_args.kwargs["release_id"] == "old"
    assert bundle.retrieval_metrics["fallback"] == "qdrant_unavailable"


@pytest.mark.asyncio
@pytest.mark.parametrize("release_id", ["old", None])
async def test_prepared_turn_freezes_tool_and_citation_release(release_id):
    repository = _repository()
    knowledge = ReleaseKnowledgeGateway(repository)
    original_tools = ToolRegistry(knowledge, Mock())
    retrieval = SimpleNamespace(retrieve=AsyncMock(return_value=EvidenceBundle(release_id=release_id)))
    engine = AssistantEngine(knowledge, api_key="", retrieval=retrieval)
    text = "Explain soil texture"
    engine.clarification = SimpleNamespace(advance=AsyncMock(return_value=SimpleNamespace(
        effective_text=text, analysis={}, pending=False, interaction={}
    )))
    command = TurnCommand(request_id="pin", actor_id="actor", channel="test",
                          conversation_id="conversation", text=text, clarification_style="direct")
    prepared = await engine.prepare(command, tools=original_tools, history=[], clarification_count=0)
    repository.active_release.return_value = "new"
    turn_tools = prepared.turn_tools
    assert turn_tools is not None and turn_tools is not original_tools
    assert original_tools.knowledge.active_release_id() == "new"
    turn_tools.recent_citations.append({"id": "turn-only"})
    assert original_tools.recent_citations == []
    if release_id:
        turn_tools.knowledge.search("soil texture", language="english")
        assert repository.hybrid_search.call_args.kwargs["release_id"] == "old"
        assert turn_tools.get_source("source")["source"]["release_id"] == "old"
    else:
        with pytest.raises(ReleaseUnavailable):
            turn_tools.knowledge.search("soil texture", language="english")
        assert turn_tools.get_source("source")["available"] is False
        repository.hybrid_search.assert_not_called()
