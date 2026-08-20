"""Persist structured iterative clarification interactions.

Revision ID: 20260819_0006
Revises: 20260812_0005
Create Date: 2026-08-19
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "20260819_0006"
down_revision: str | None = "20260812_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE messages
            ADD COLUMN interaction_json JSONB NOT NULL DEFAULT '{}'::jsonb;
        ALTER TABLE messages
            ADD CONSTRAINT messages_interaction_json_object_check
            CHECK (jsonb_typeof(interaction_json) = 'object');
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM messages
                WHERE interaction_json <> '{}'::jsonb
                LIMIT 1
            ) THEN
                RAISE EXCEPTION
                    'refusing clarification downgrade while interaction data exists';
            END IF;
        END;
        $$;

        ALTER TABLE messages
            DROP CONSTRAINT messages_interaction_json_object_check;
        ALTER TABLE messages DROP COLUMN interaction_json;
        """
    )
