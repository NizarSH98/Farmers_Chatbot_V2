"""Database migration state used by hosted startup readiness checks."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

EXPECTED_DATABASE_REVISION = "20260812_0004"


class MigrationStateError(RuntimeError):
    """Raised when a managed database is not at the application schema head."""


def current_database_revision(
    database_url: str,
    *,
    connect: Callable[..., Any] | None = None,
) -> str:
    """Read the single Alembic revision without exposing connection details."""

    if not database_url.startswith(("postgres://", "postgresql://")):
        raise MigrationStateError("managed schema checks require PostgreSQL")
    if connect is None:
        try:
            from psycopg import connect as psycopg_connect
        except ImportError as exc:  # pragma: no cover - deployment dependency
            raise MigrationStateError("psycopg is required for schema checks") from exc
        connect = psycopg_connect

    try:
        with (
            connect(database_url, connect_timeout=5) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute("SELECT version_num FROM alembic_version")
            rows = cursor.fetchall()
    except Exception as exc:
        raise MigrationStateError(
            "database migration state is unavailable; run `alembic upgrade head`"
        ) from exc

    if len(rows) != 1 or not rows[0] or not rows[0][0]:
        raise MigrationStateError("database must have exactly one Alembic revision")
    return str(rows[0][0])


def require_database_revision(
    database_url: str,
    expected_revision: str = EXPECTED_DATABASE_REVISION,
    *,
    connect: Callable[..., Any] | None = None,
) -> str:
    """Fail closed unless the managed database is at the expected revision."""

    current = current_database_revision(database_url, connect=connect)
    if current != expected_revision:
        raise MigrationStateError(
            f"database revision is {current!r}; expected {expected_revision!r}; "
            "run `alembic upgrade head` before starting the service"
        )
    return current
