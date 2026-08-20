from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any, Self

import pytest

from farmers_chatbot.migration_status import (
    EXPECTED_DATABASE_REVISION,
    MigrationStateError,
    current_database_revision,
    require_database_revision,
)
from farmers_chatbot.pilot_store import PilotStore
from farmers_chatbot.storage_backends import configured_file_storage


class _Cursor:
    def __init__(self, rows: list[tuple[str]]) -> None:
        self.rows = rows
        self.statement = ""

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def execute(self, statement: str) -> None:
        self.statement = statement

    def fetchall(self) -> list[tuple[str]]:
        return self.rows


class _Connection:
    def __init__(self, rows: list[tuple[str]]) -> None:
        self.cursor_instance = _Cursor(rows)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def cursor(self) -> _Cursor:
        return self.cursor_instance


def _connect_with(rows: list[tuple[str]]) -> Any:
    def connect(url: str, *, connect_timeout: int) -> _Connection:
        assert url.startswith("postgresql://")
        assert connect_timeout == 5
        return _Connection(rows)

    return connect


def test_reads_exactly_one_alembic_revision() -> None:
    revision = current_database_revision(
        "postgresql://db.example/raise",
        connect=_connect_with([(EXPECTED_DATABASE_REVISION,)]),
    )
    assert revision == EXPECTED_DATABASE_REVISION


@pytest.mark.parametrize("rows", [[], [("one",), ("two",)]])
def test_rejects_missing_or_multiple_revision_rows(rows: list[tuple[str]]) -> None:
    with pytest.raises(MigrationStateError, match="exactly one"):
        current_database_revision(
            "postgresql://db.example/raise",
            connect=_connect_with(rows),
        )


def test_rejects_revision_mismatch() -> None:
    with pytest.raises(MigrationStateError, match="alembic upgrade head"):
        require_database_revision(
            "postgresql://db.example/raise",
            connect=_connect_with([("old-revision",)]),
        )


def test_store_refuses_any_non_postgresql_database_url() -> None:
    """Schema versioning lives in Alembic, so there is no second backend."""

    with pytest.raises(RuntimeError, match="requires a PostgreSQL DATABASE_URL"):
        PilotStore(database_url="sqlite:///data/pilot.sqlite3")
    with pytest.raises(RuntimeError, match="requires a PostgreSQL DATABASE_URL"):
        PilotStore(database_url="")


def test_hosted_storage_refuses_local_fallback(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "pilot")
    monkeypatch.setattr("farmers_chatbot.storage_backends.SUPABASE_URL", "")
    monkeypatch.setattr(
        "farmers_chatbot.storage_backends.SUPABASE_SERVICE_ROLE_KEY", ""
    )
    with pytest.raises(RuntimeError, match="local fallback is disabled"):
        configured_file_storage()


def test_legacy_baseline_files_are_checksum_pinned() -> None:
    root = Path(__file__).resolve().parents[1]
    revision_path = (
        root
        / "migrations"
        / "versions"
        / "20260811_0001_legacy_schema_baseline.py"
    )
    spec = importlib.util.spec_from_file_location("raise_legacy_baseline", revision_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for filename, checksum in module._LEGACY_MIGRATIONS:
        assert module._legacy_sql(filename, checksum)
