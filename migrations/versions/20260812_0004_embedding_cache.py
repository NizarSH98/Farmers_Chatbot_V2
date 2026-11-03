"""Add approved embedding cache and permit model-specific release rebuilds.

Revision ID: 20260812_0004
Revises: 20260811_0003
Create Date: 2026-08-12
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "20260812_0004"
down_revision: str | None = "20260811_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        r"""
        ALTER TABLE knowledge_releases
            DROP CONSTRAINT knowledge_releases_version_key;
        CREATE UNIQUE INDEX uq_knowledge_release_build
            ON knowledge_releases (
                version, publication_scope, review_policy, embedding_model,
                embedding_dimensions, source_manifest_sha256
            );

        CREATE TABLE graph_embedding_cache (
            embedding_model TEXT NOT NULL,
            embedding_dimensions INTEGER NOT NULL
                CHECK (embedding_dimensions IN (768, 1536)),
            input_type TEXT NOT NULL
                CHECK (input_type IN ('search_document', 'search_query')),
            content_sha256 TEXT NOT NULL
                CHECK (content_sha256 ~ '^[0-9a-f]{64}$'),
            embedding vector NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (
                embedding_model, embedding_dimensions, input_type, content_sha256
            ),
            CHECK (vector_dims(embedding) = embedding_dimensions)
        );
        """
    )


def downgrade() -> None:
    op.execute(
        r"""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM graph_embedding_cache LIMIT 1) THEN
                RAISE EXCEPTION
                    'refusing embedding-cache downgrade while cached vectors exist';
            END IF;
            IF EXISTS (
                SELECT version
                FROM knowledge_releases
                GROUP BY version
                HAVING count(*) > 1
            ) THEN
                RAISE EXCEPTION
                    'refusing downgrade while release versions are duplicated';
            END IF;
        END;
        $$;

        DROP TABLE graph_embedding_cache;
        DROP INDEX uq_knowledge_release_build;
        ALTER TABLE knowledge_releases
            ADD CONSTRAINT knowledge_releases_version_key UNIQUE (version);
        """
    )

