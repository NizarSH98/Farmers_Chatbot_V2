"""Remove the obsolete vendor-auth identity column.

Revision ID: 20260901_0007
Revises: 20260819_0006
Create Date: 2026-09-01
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "20260901_0007"
down_revision: str | None = "20260819_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        DROP INDEX IF EXISTS idx_users_auth_user_id;
        ALTER TABLE users DROP COLUMN IF EXISTS auth_user_id;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE users ADD COLUMN IF NOT EXISTS auth_user_id TEXT;
        CREATE UNIQUE INDEX IF NOT EXISTS idx_users_auth_user_id
            ON users(auth_user_id) WHERE auth_user_id IS NOT NULL;
        """
    )
