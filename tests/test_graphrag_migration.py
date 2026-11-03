from __future__ import annotations

import importlib.util
from pathlib import Path


def _revision_module():
    path = (
        Path(__file__).resolve().parents[1]
        / "migrations"
        / "versions"
        / "20260811_0003_versioned_graphrag.py"
    )
    spec = importlib.util.spec_from_file_location("raise_graphrag_revision", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path.read_text(encoding="utf-8")


def test_graphrag_revision_follows_turn_coordinator() -> None:
    module, _ = _revision_module()
    assert module.revision == "20260811_0003"
    assert module.down_revision == "20260811_0002"


def test_schema_contains_release_graph_provenance_and_tenant_boundaries() -> None:
    _, sql = _revision_module()
    for required in (
        "knowledge_releases",
        "active_knowledge_releases",
        "knowledge_release_activations",
        "graph_ingestion_runs",
        "graph_sources",
        "graph_documents",
        "graph_chunks",
        "graph_entities",
        "graph_entity_aliases",
        "graph_claims",
        "graph_relations",
        "graph_evidence_links",
        "project_rag_chunks",
        "project_chunk_scope_matches_document",
        "graph_relation_has_evidence",
        "graph_claim_has_evidence",
        "knowledge_release_seal_integrity",
        "active_release_integrity",
        "hybrid_search_knowledge_v2",
        "embedding::vector(768)",
        "embedding::vector(1536)",
    ):
        assert required in sql


def test_schema_refuses_data_destroying_downgrade() -> None:
    _, sql = _revision_module()
    assert "refusing GraphRAG downgrade while release or project data exists" in sql
