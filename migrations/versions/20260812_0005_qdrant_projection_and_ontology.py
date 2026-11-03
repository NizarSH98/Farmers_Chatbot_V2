"""Add Qdrant projection state, graph metrics, editor lineage, and ontology v0.3.

Revision ID: 20260812_0005
Revises: 20260812_0004
Create Date: 2026-08-12
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "20260812_0005"
down_revision: str | None = "20260812_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ENTITY_TYPES = (
    "crop", "variety", "animal", "production_stage", "symptom", "pest",
    "disease", "practice", "input", "nutrient", "soil", "water", "climate",
    "season", "location", "farm_system", "equipment", "measurement", "unit",
    "product", "value_chain_actor", "organization", "service", "market",
    "financial_instrument", "opportunity", "certification", "regulation",
    "risk", "cost", "sustainability_impact", "outcome",
)

RELATION_TYPES = (
    "applies_to", "has_stage", "has_symptom", "located_in", "requires_context",
    "depends_on", "measured_by", "has_unit", "targets", "affects", "may_cause",
    "may_be_confused_with", "controls", "prevents", "supports_action", "increases",
    "decreases", "produces", "sold_to", "provided_by", "costs", "benefits",
    "alternative_to", "compatible_with", "contraindicated_with", "prohibits",
    "escalates_to", "requires_live_source", "supported_by", "supersedes",
    "conflicts_with", "valid_during", "related_to",
)


def _quoted(values: tuple[str, ...]) -> str:
    return ", ".join(f"'{value}'" for value in values)


def upgrade() -> None:
    op.execute(
        f"""
        ALTER TABLE graph_entities DROP CONSTRAINT graph_entities_entity_type_check;
        ALTER TABLE graph_entities ADD CONSTRAINT graph_entities_entity_type_check
            CHECK (entity_type IN ({_quoted(ENTITY_TYPES)}));

        ALTER TABLE graph_relations DROP CONSTRAINT graph_relations_predicate_check;
        ALTER TABLE graph_relations ADD CONSTRAINT graph_relations_predicate_check
            CHECK (predicate IN ({_quoted(RELATION_TYPES)}));

        ALTER TABLE graph_embedding_cache
            DROP CONSTRAINT graph_embedding_cache_embedding_dimensions_check;
        ALTER TABLE graph_embedding_cache
            ADD CONSTRAINT graph_embedding_cache_embedding_dimensions_check
            CHECK (embedding_dimensions IN (384, 768, 1024, 1536));

        CREATE INDEX idx_graph_chunks_embedding_384
            ON graph_chunks USING hnsw ((embedding::vector(384)) vector_cosine_ops)
            WHERE embedding IS NOT NULL AND embedding_dimensions = 384;
        CREATE INDEX idx_graph_chunks_embedding_1024
            ON graph_chunks USING hnsw ((embedding::vector(1024)) vector_cosine_ops)
            WHERE embedding IS NOT NULL AND embedding_dimensions = 1024;
        CREATE INDEX idx_project_rag_chunks_embedding_384
            ON project_rag_chunks USING hnsw ((embedding::vector(384)) vector_cosine_ops)
            WHERE embedding IS NOT NULL AND embedding_dimensions = 384;
        CREATE INDEX idx_project_rag_chunks_embedding_1024
            ON project_rag_chunks USING hnsw ((embedding::vector(1024)) vector_cosine_ops)
            WHERE embedding IS NOT NULL AND embedding_dimensions = 1024;

        CREATE TABLE knowledge_release_projections (
            release_id TEXT NOT NULL REFERENCES knowledge_releases(id),
            target TEXT NOT NULL CHECK (target IN ('qdrant')),
            state TEXT NOT NULL DEFAULT 'pending'
                CHECK (state IN ('pending', 'building', 'ready', 'failed', 'stale')),
            evidence_collection TEXT NOT NULL,
            entity_collection TEXT NOT NULL,
            manifest_sha256 TEXT CHECK (
                manifest_sha256 IS NULL OR manifest_sha256 ~ '^[0-9a-f]{{64}}$'
            ),
            evidence_points INTEGER NOT NULL DEFAULT 0 CHECK (evidence_points >= 0),
            entity_points INTEGER NOT NULL DEFAULT 0 CHECK (entity_points >= 0),
            embedding_model TEXT NOT NULL,
            embedding_dimensions INTEGER NOT NULL
                CHECK (embedding_dimensions IN (384, 768, 1024, 1536)),
            last_error TEXT,
            started_at TIMESTAMPTZ,
            ready_at TIMESTAMPTZ,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (release_id, target)
        );
        CREATE INDEX idx_release_projections_state
            ON knowledge_release_projections(state, updated_at);

        CREATE TABLE knowledge_projection_outbox (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            release_id TEXT NOT NULL REFERENCES knowledge_releases(id),
            event_type TEXT NOT NULL
                CHECK (event_type IN ('project', 'activate', 'rollback', 'reconcile')),
            payload_json JSONB NOT NULL DEFAULT '{{}}'::jsonb
                CHECK (jsonb_typeof(payload_json) = 'object'),
            state TEXT NOT NULL DEFAULT 'pending'
                CHECK (state IN ('pending', 'processing', 'completed', 'failed')),
            attempts INTEGER NOT NULL DEFAULT 0 CHECK (attempts >= 0),
            last_error TEXT,
            available_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            completed_at TIMESTAMPTZ,
            UNIQUE (release_id, event_type)
        );
        CREATE INDEX idx_projection_outbox_pending
            ON knowledge_projection_outbox(state, available_at, id)
            WHERE state IN ('pending', 'failed');

        CREATE TABLE graph_entity_metrics (
            release_id TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            pagerank_global DOUBLE PRECISION NOT NULL DEFAULT 0
                CHECK (pagerank_global >= 0 AND pagerank_global <= 1),
            degree INTEGER NOT NULL DEFAULT 0 CHECK (degree >= 0),
            evidence_count INTEGER NOT NULL DEFAULT 0 CHECK (evidence_count >= 0),
            component_id TEXT,
            computed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (release_id, entity_id),
            FOREIGN KEY (release_id, entity_id)
                REFERENCES graph_entities(release_id, id)
        );
        CREATE INDEX idx_graph_entity_metrics_rank
            ON graph_entity_metrics(release_id, pagerank_global DESC);

        CREATE TABLE knowledge_editors (
            user_id TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            assigned_by TEXT REFERENCES users(id) ON DELETE SET NULL,
            assigned_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            revoked_at TIMESTAMPTZ
        );

        CREATE TABLE knowledge_change_proposals (
            id TEXT PRIMARY KEY,
            base_release_id TEXT NOT NULL REFERENCES knowledge_releases(id),
            proposed_release_id TEXT REFERENCES knowledge_releases(id),
            editor_user_id TEXT NOT NULL REFERENCES users(id),
            record_type TEXT NOT NULL
                CHECK (record_type IN ('document', 'claim', 'relation', 'translation')),
            record_id TEXT NOT NULL,
            operation TEXT NOT NULL CHECK (operation IN ('create', 'update', 'retire')),
            patch_json JSONB NOT NULL CHECK (jsonb_typeof(patch_json) = 'object'),
            state TEXT NOT NULL DEFAULT 'proposed'
                CHECK (state IN ('proposed', 'accepted', 'rejected', 'superseded')),
            reviewer_user_id TEXT REFERENCES users(id),
            review_note TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            reviewed_at TIMESTAMPTZ
        );
        CREATE INDEX idx_change_proposals_review
            ON knowledge_change_proposals(state, created_at);

        CREATE OR REPLACE FUNCTION raise_enqueue_projection()
        RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            IF NEW.state = 'ready' AND OLD.state IS DISTINCT FROM 'ready' THEN
                INSERT INTO knowledge_projection_outbox (
                    release_id, event_type, payload_json
                ) VALUES (NEW.id, 'project', jsonb_build_object('release_id', NEW.id))
                ON CONFLICT (release_id, event_type) DO NOTHING;
            END IF;
            RETURN NEW;
        END;
        $$;
        CREATE TRIGGER trg_enqueue_qdrant_projection
            AFTER UPDATE OF state ON knowledge_releases
            FOR EACH ROW EXECUTE FUNCTION raise_enqueue_projection();
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM knowledge_change_proposals LIMIT 1)
               OR EXISTS (SELECT 1 FROM knowledge_release_projections LIMIT 1)
               OR EXISTS (SELECT 1 FROM graph_entity_metrics LIMIT 1) THEN
                RAISE EXCEPTION
                    'refusing Qdrant/ontology downgrade while RC data exists';
            END IF;
        END;
        $$;

        DROP TRIGGER trg_enqueue_qdrant_projection ON knowledge_releases;
        DROP FUNCTION raise_enqueue_projection();
        DROP TABLE knowledge_change_proposals;
        DROP TABLE knowledge_editors;
        DROP TABLE graph_entity_metrics;
        DROP TABLE knowledge_projection_outbox;
        DROP TABLE knowledge_release_projections;
        DROP INDEX idx_project_rag_chunks_embedding_1024;
        DROP INDEX idx_project_rag_chunks_embedding_384;
        DROP INDEX idx_graph_chunks_embedding_1024;
        DROP INDEX idx_graph_chunks_embedding_384;

        ALTER TABLE graph_embedding_cache
            DROP CONSTRAINT graph_embedding_cache_embedding_dimensions_check;
        ALTER TABLE graph_embedding_cache
            ADD CONSTRAINT graph_embedding_cache_embedding_dimensions_check
            CHECK (embedding_dimensions IN (768, 1536));

        ALTER TABLE graph_relations DROP CONSTRAINT graph_relations_predicate_check;
        ALTER TABLE graph_relations ADD CONSTRAINT graph_relations_predicate_check
            CHECK (predicate IN (
                'applies_to', 'requires_context', 'depends_on', 'may_cause',
                'may_be_confused_with', 'supports_action', 'prohibits',
                'escalates_to', 'requires_live_source', 'supported_by',
                'supersedes', 'conflicts_with', 'related_to'
            ));

        ALTER TABLE graph_entities DROP CONSTRAINT graph_entities_entity_type_check;
        ALTER TABLE graph_entities ADD CONSTRAINT graph_entities_entity_type_check
            CHECK (entity_type IN (
                'crop', 'variety', 'animal', 'production_stage', 'symptom',
                'pest', 'disease', 'practice', 'input', 'soil', 'water',
                'climate', 'season', 'location', 'organization', 'service',
                'market', 'regulation', 'risk', 'cost', 'sustainability_impact'
            ));
        """
    )
