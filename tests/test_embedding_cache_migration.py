"""Schema-contract checks for approved cross-release embedding reuse."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from farmers_chatbot.migration_status import EXPECTED_DATABASE_REVISION


def _migration():
    path = (
        Path(__file__).parents[1]
        / "migrations"
        / "versions"
        / "20260812_0004_embedding_cache.py"
    )
    spec = importlib.util.spec_from_file_location("embedding_cache_migration", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path.read_text(encoding="utf-8")


def test_embedding_cache_is_the_expected_linear_head() -> None:
    module, _ = _migration()
    assert module.revision == "20260812_0004"
    assert EXPECTED_DATABASE_REVISION == "20260819_0006"
    assert module.down_revision == "20260811_0003"


def test_embedding_cache_key_and_dimension_guards_are_explicit() -> None:
    _, source = _migration()
    assert "CREATE TABLE graph_embedding_cache" in source
    assert "embedding_model, embedding_dimensions, input_type, content_sha256" in source
    assert "vector_dims(embedding) = embedding_dimensions" in source
    assert "embedding_dimensions IN (768, 1536)" in source
    assert "refusing embedding-cache downgrade while cached vectors exist" in source


def test_release_version_can_be_rebuilt_for_a_different_approved_index() -> None:
    _, source = _migration()
    assert "DROP CONSTRAINT knowledge_releases_version_key" in source
    assert "CREATE UNIQUE INDEX uq_knowledge_release_build" in source
    assert "source_manifest_sha256" in source

