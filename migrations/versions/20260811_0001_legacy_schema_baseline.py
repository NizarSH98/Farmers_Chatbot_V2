"""Adopt the existing pilot and web schema without replacing stored data.

Revision ID: 20260811_0001
Revises: None
Create Date: 2026-08-11

This first revision intentionally executes the two previously deployed, idempotent
SQL migrations. On an existing pilot database it only verifies/adds missing schema
objects before Alembic records the revision. On an empty PostgreSQL database it
creates the same schema. The legacy files are checksum-pinned and must remain
immutable; subsequent changes belong in new Alembic revisions.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from pathlib import Path

from alembic import context, op

revision: str = "20260811_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_LEGACY_MIGRATIONS = (
    (
        "001_pilot_schema.sql",
        "c23c8563826b9472c828322f35318e8089ba4a206cce058825dbb163300ce3a1",
    ),
    (
        "002_web_platform.sql",
        "b2088ef2ad2a125dd246c2fe2ede64f186d228ee3bdaef45678dd0c8fb30e5cd",
    ),
)


def _legacy_sql(filename: str, expected_sha256: str) -> str:
    path = Path(__file__).resolve().parents[1] / filename
    content = path.read_bytes()
    actual_sha256 = hashlib.sha256(content).hexdigest()
    if actual_sha256 != expected_sha256:
        raise RuntimeError(
            f"Legacy migration {filename} changed after baseline creation; "
            "restore it and add a new Alembic revision instead."
        )
    return content.decode("utf-8")


def upgrade() -> None:
    connection = op.get_bind()
    for filename, sha256 in _LEGACY_MIGRATIONS:
        sql = _legacy_sql(filename, sha256)
        if context.is_offline_mode():
            op.execute(sql)
        else:
            connection.exec_driver_sql(sql)


def downgrade() -> None:
    # This is an adoption baseline for databases that may contain pilot records.
    # Removing legacy tables would destroy those records. Downgrading therefore
    # removes only Alembic's revision marker; a later upgrade safely re-adopts the
    # unchanged, idempotent schema.
    pass
