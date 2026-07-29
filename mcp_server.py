"""MCP server exposing bounded RAISE knowledge and monitoring tools.

Run locally:
    python mcp_server.py

The default stdio transport is intentionally local. Do not expose an unauthenticated
HTTP transport on a public interface.
"""

from __future__ import annotations

import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from farmers_chatbot.artifacts import ArtifactService
from farmers_chatbot.auth import development_identity
from farmers_chatbot.config import ENABLE_TRUSTED_WEB_SEARCH
from farmers_chatbot.documents import search_project_chunks
from farmers_chatbot.knowledge import KnowledgeIndex
from farmers_chatbot.pilot_store import PilotStore
from farmers_chatbot.storage import EvidenceStore
from farmers_chatbot.storage_backends import configured_file_storage
from farmers_chatbot.tools import ToolRegistry
from farmers_chatbot.trusted_sources import TrustedSourceClient

knowledge = KnowledgeIndex.from_directory()
store = EvidenceStore()
pilot_store = PilotStore()
file_storage = configured_file_storage()
mcp_user = pilot_store.upsert_user(development_identity())
artifact_service = ArtifactService(
    pilot_store,
    file_storage,
    owner_user_id=mcp_user["id"],
)
trusted_client = TrustedSourceClient(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    enabled=ENABLE_TRUSTED_WEB_SEARCH,
)
registry = ToolRegistry(
    knowledge,
    store,
    trusted_client=trusted_client,
    artifact_service=artifact_service,
)
mcp = FastMCP(
    "RAISE Akkar Agricultural Knowledge",
    instructions=(
        "Use these tools for sourced Akkar/Lebanon agricultural knowledge and "
        "evidence-based RAISE logframe status. Dynamic facts require dated approved sources."
    ),
)


@mcp.tool()
def search_knowledge(
    query: str,
    language: str | None = None,
    top_k: int = 5,
) -> dict[str, Any]:
    """Search bilingual, source-traceable agricultural knowledge."""

    return registry.search_knowledge(query, language, top_k)


@mcp.tool()
def get_source(source_id: str) -> dict[str, Any]:
    """Get publisher, URL, topic, and review metadata for a source ID."""

    return registry.get_source(source_id)


@mcp.tool()
def get_verified_source(
    source_id: str = "",
    url: str = "",
) -> dict[str, Any]:
    """Verify an internal source ID or a trusted-registry HTTPS URL."""

    return registry.get_verified_source(source_id, url)


@mcp.tool()
def search_project_knowledge(
    project_id: str,
    query: str,
    top_k: int = 5,
) -> dict[str, Any]:
    """Search documents owned by the local MCP pilot identity."""

    chunks = pilot_store.list_project_chunks(mcp_user["id"], project_id)
    results = search_project_chunks(chunks, query, top_k=top_k)
    return {
        "query": query,
        "source_warning": "User-provided; not approved authority.",
        "results": [result.to_dict() for result in results],
    }


@mcp.tool()
def search_trusted_sources(
    query: str,
    category: str = "auto",
) -> dict[str, Any]:
    """Search the server-controlled trusted institutional domain registry."""

    return registry.search_trusted_sources(query, category)


@mcp.tool()
def convert_agricultural_units(
    value: float,
    from_unit: str,
    to_unit: str,
) -> dict[str, Any]:
    """Convert supported agricultural area, volume, or mass units."""

    return registry.convert_agricultural_units(value, from_unit, to_unit)


@mcp.tool()
def generate_farm_action_plan(
    title: str,
    context: str,
    actions: list[str],
    language: str = "english",
    assumptions: list[str] | None = None,
    sources: list[str] | None = None,
) -> dict[str, Any]:
    """Generate a bounded DOCX farm action plan in private local storage."""

    return registry.generate_farm_action_plan(
        title=title,
        context=context,
        actions=actions,
        language=language,
        assumptions=assumptions or [],
        sources=sources or [],
    )


@mcp.tool()
def generate_inspection_checklist(
    title: str,
    context: str,
    checks: list[str],
    language: str = "english",
    escalation_signs: list[str] | None = None,
    sources: list[str] | None = None,
) -> dict[str, Any]:
    """Generate a bounded DOCX field inspection checklist."""

    return registry.generate_inspection_checklist(
        title=title,
        context=context,
        checks=checks,
        language=language,
        escalation_signs=escalation_signs or [],
        sources=sources or [],
    )


@mcp.tool()
def generate_crop_calendar(
    title: str,
    entries: list[dict[str, Any]],
    language: str = "english",
    assumptions: list[str] | None = None,
    sources: list[str] | None = None,
) -> dict[str, Any]:
    """Generate an XLSX decision-window crop calendar."""

    return registry.generate_crop_calendar(
        title=title,
        entries=entries,
        language=language,
        assumptions=assumptions or [],
        sources=sources or [],
    )


@mcp.tool()
def generate_expert_referral_brief(
    title: str,
    situation: str,
    observations: list[str],
    question_for_expert: str,
    language: str = "english",
    urgent_signs: list[str] | None = None,
    sources: list[str] | None = None,
) -> dict[str, Any]:
    """Generate a bounded DOCX expert-referral brief."""

    return registry.generate_expert_referral_brief(
        title=title,
        situation=situation,
        observations=observations,
        question_for_expert=question_for_expert,
        language=language,
        urgent_signs=urgent_signs or [],
        sources=sources or [],
    )


@mcp.tool()
def calculate_enterprise_budget(
    title: str,
    currency: str,
    costs: list[dict[str, Any]],
    revenues: list[dict[str, Any]],
    assumptions: list[str] | None = None,
    sources: list[str] | None = None,
) -> dict[str, Any]:
    """Calculate a scenario budget and generate a formula-based XLSX."""

    return registry.calculate_enterprise_budget(
        title=title,
        currency=currency,
        costs=costs,
        revenues=revenues,
        assumptions=assumptions or [],
        sources=sources or [],
    )


@mcp.tool()
def get_logframe_status() -> dict[str, Any]:
    """Get RAISE build-readiness and contractual-evidence status."""

    return registry.get_logframe_status()


@mcp.tool()
def record_feedback(
    session_id: str,
    category: str,
    comment: str,
    consent: bool,
    rating: int | None = None,
    language: str | None = None,
) -> dict[str, Any]:
    """Record consent-aware, non-sensitive pilot feedback."""

    return registry.record_feedback(
        session_id=session_id,
        category=category,
        comment=comment,
        consent=consent,
        rating=rating,
        language=language,
    )


@mcp.resource("raise-source://{source_id}")
def source_resource(source_id: str) -> str:
    """Read a knowledge source record by stable ID."""

    return registry.execute("get_source", {"source_id": source_id})


if __name__ == "__main__":
    mcp.run(transport="stdio")
