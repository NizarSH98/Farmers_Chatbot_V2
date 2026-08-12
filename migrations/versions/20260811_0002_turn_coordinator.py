"""Add atomic idempotent turn reservations and exact provider accounting.

Revision ID: 20260811_0002
Revises: 20260811_0001
Create Date: 2026-08-11
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "20260811_0002"
down_revision: str | None = "20260811_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE assistant_turns
            ADD COLUMN IF NOT EXISTS request_id TEXT,
            ADD COLUMN IF NOT EXISTS payload_sha256 TEXT,
            ADD COLUMN IF NOT EXISTS channel TEXT NOT NULL DEFAULT 'web',
            ADD COLUMN IF NOT EXISTS terminal_sequence INTEGER;

        CREATE UNIQUE INDEX IF NOT EXISTS idx_assistant_turns_request
            ON assistant_turns(owner_user_id, request_id)
            WHERE request_id IS NOT NULL;

        ALTER TABLE query_events
            ADD COLUMN IF NOT EXISTS turn_id TEXT REFERENCES assistant_turns(id)
                ON DELETE SET NULL,
            ADD COLUMN IF NOT EXISTS payload_sha256 TEXT,
            ADD COLUMN IF NOT EXISTS query_status TEXT NOT NULL DEFAULT 'reserved',
            ADD COLUMN IF NOT EXISTS reserved_cost_usd NUMERIC(12, 6)
                NOT NULL DEFAULT 0,
            ADD COLUMN IF NOT EXISTS finalized_at TIMESTAMPTZ;

        UPDATE query_events
        SET query_status = CASE
            WHEN duration_ms IS NULL THEN 'reserved'
            WHEN success THEN 'completed'
            ELSE 'failed'
        END;

        CREATE UNIQUE INDEX IF NOT EXISTS idx_query_events_request
            ON query_events(user_id, request_id)
            WHERE request_id IS NOT NULL;

        CREATE TABLE IF NOT EXISTS provider_calls (
            id TEXT PRIMARY KEY,
            turn_id TEXT NOT NULL REFERENCES assistant_turns(id) ON DELETE CASCADE,
            request_id TEXT NOT NULL,
            sequence INTEGER NOT NULL,
            stage TEXT NOT NULL,
            model TEXT NOT NULL,
            duration_ms INTEGER NOT NULL,
            outcome TEXT NOT NULL,
            prompt_tokens INTEGER,
            completion_tokens INTEGER,
            cost_usd NUMERIC(12, 6),
            error_type TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(turn_id, sequence)
        );
        CREATE INDEX IF NOT EXISTS idx_provider_calls_request
            ON provider_calls(request_id, sequence);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE IF EXISTS provider_calls;
        DROP INDEX IF EXISTS idx_query_events_request;
        ALTER TABLE query_events
            DROP COLUMN IF EXISTS finalized_at,
            DROP COLUMN IF EXISTS reserved_cost_usd,
            DROP COLUMN IF EXISTS query_status,
            DROP COLUMN IF EXISTS payload_sha256,
            DROP COLUMN IF EXISTS turn_id;
        DROP INDEX IF EXISTS idx_assistant_turns_request;
        ALTER TABLE assistant_turns
            DROP COLUMN IF EXISTS terminal_sequence,
            DROP COLUMN IF EXISTS channel,
            DROP COLUMN IF EXISTS payload_sha256,
            DROP COLUMN IF EXISTS request_id;
        """
    )
