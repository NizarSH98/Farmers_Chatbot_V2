"""Give every account a stable pseudonymous participant code.

Revision ID: 20261110_0008
Revises: 20260901_0007
Create Date: 2026-11-10

The research retention window keeps pseudonymous interaction records after the
email and name of an inactive account are removed. The participant code is the
link that survives: the field team records it in the controlled stakeholder
tracker, so a record can be referred back to a person without the database
holding a direct identifier. Existing accounts are backfilled.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "20261110_0008"
down_revision: str | None = "20260901_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE users ADD COLUMN IF NOT EXISTS participant_code TEXT;
        -- Same unambiguous alphabet as PilotStore._unused_participant_code
        -- (no 0/O, 1/I/L). The correlated id reference makes Postgres draw
        -- fresh random characters for every row.
        UPDATE users u
        SET participant_code = 'RAISE-' || (
            SELECT string_agg(
                substr(
                    '23456789ABCDEFGHJKMNPQRSTUVWXYZ',
                    1 + floor(random() * 31)::int,
                    1
                ),
                ''
            )
            FROM generate_series(1, 6) AS position
            WHERE u.id IS NOT NULL
        )
        WHERE participant_code IS NULL;
        ALTER TABLE users ALTER COLUMN participant_code SET NOT NULL;
        CREATE UNIQUE INDEX IF NOT EXISTS idx_users_participant_code
            ON users(participant_code);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP INDEX IF EXISTS idx_users_participant_code;
        ALTER TABLE users DROP COLUMN IF EXISTS participant_code;
        """
    )
