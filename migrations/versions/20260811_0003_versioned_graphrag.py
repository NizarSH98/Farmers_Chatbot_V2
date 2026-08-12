"""Add immutable versioned hybrid GraphRAG storage.

Revision ID: 20260811_0003
Revises: 20260811_0002
Create Date: 2026-08-11
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "20260811_0003"
down_revision: str | None = "20260811_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        r"""
        CREATE TABLE knowledge_releases (
            id TEXT PRIMARY KEY,
            version TEXT NOT NULL UNIQUE,
            state TEXT NOT NULL DEFAULT 'building'
                CHECK (state IN ('building', 'ready', 'failed')),
            publication_scope TEXT NOT NULL
                CHECK (publication_scope IN ('internal', 'pilot', 'production')),
            review_policy TEXT NOT NULL
                CHECK (review_policy IN ('draft_allowed', 'approved_only')),
            embedding_model TEXT NOT NULL,
            embedding_dimensions INTEGER NOT NULL
                CHECK (embedding_dimensions BETWEEN 128 AND 4096),
            source_manifest_sha256 TEXT NOT NULL
                CHECK (source_manifest_sha256 ~ '^[0-9a-f]{64}$'),
            metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb
                CHECK (jsonb_typeof(metadata_json) = 'object'),
            created_by TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            sealed_at TIMESTAMPTZ,
            failed_at TIMESTAMPTZ,
            failure_reason TEXT,
            CHECK (
                (state = 'building' AND sealed_at IS NULL AND failed_at IS NULL)
                OR (state = 'ready' AND sealed_at IS NOT NULL AND failed_at IS NULL)
                OR (state = 'failed' AND sealed_at IS NULL AND failed_at IS NOT NULL)
            )
        );

        CREATE TABLE active_knowledge_releases (
            deployment_scope TEXT PRIMARY KEY
                CHECK (deployment_scope IN ('internal', 'pilot', 'production')),
            release_id TEXT NOT NULL REFERENCES knowledge_releases(id),
            activated_by TEXT,
            activated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE knowledge_release_activations (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            deployment_scope TEXT NOT NULL
                CHECK (deployment_scope IN ('internal', 'pilot', 'production')),
            release_id TEXT NOT NULL REFERENCES knowledge_releases(id),
            previous_release_id TEXT REFERENCES knowledge_releases(id),
            activated_by TEXT,
            reason TEXT NOT NULL DEFAULT 'activate',
            activated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CHECK (release_id IS DISTINCT FROM previous_release_id)
        );
        CREATE INDEX idx_release_activations_scope_time
            ON knowledge_release_activations(deployment_scope, id DESC);

        CREATE TABLE graph_ingestion_runs (
            id TEXT PRIMARY KEY,
            release_id TEXT NOT NULL REFERENCES knowledge_releases(id),
            input_sha256 TEXT NOT NULL CHECK (input_sha256 ~ '^[0-9a-f]{64}$'),
            state TEXT NOT NULL DEFAULT 'running'
                CHECK (state IN ('running', 'completed', 'failed')),
            parser_version TEXT NOT NULL,
            stats_json JSONB NOT NULL DEFAULT '{}'::jsonb
                CHECK (jsonb_typeof(stats_json) = 'object'),
            error_type TEXT,
            started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            completed_at TIMESTAMPTZ,
            UNIQUE(release_id, input_sha256),
            CHECK (
                (state = 'running' AND completed_at IS NULL)
                OR (state IN ('completed', 'failed') AND completed_at IS NOT NULL)
            )
        );

        CREATE TABLE graph_sources (
            release_id TEXT NOT NULL REFERENCES knowledge_releases(id),
            id TEXT NOT NULL,
            source_key TEXT NOT NULL,
            title TEXT NOT NULL,
            publisher TEXT NOT NULL,
            source_kind TEXT NOT NULL,
            evidence_class TEXT NOT NULL,
            url TEXT,
            license TEXT,
            observed_at TIMESTAMPTZ,
            effective_from TIMESTAMPTZ,
            expires_at TIMESTAMPTZ,
            content_sha256 TEXT CHECK (
                content_sha256 IS NULL OR content_sha256 ~ '^[0-9a-f]{64}$'
            ),
            metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb
                CHECK (jsonb_typeof(metadata_json) = 'object'),
            PRIMARY KEY(release_id, id),
            UNIQUE(release_id, source_key),
            CHECK (expires_at IS NULL OR observed_at IS NULL OR expires_at > observed_at)
        );

        CREATE TABLE graph_documents (
            release_id TEXT NOT NULL,
            id TEXT NOT NULL,
            source_id TEXT NOT NULL,
            title TEXT NOT NULL,
            language TEXT NOT NULL,
            content_sha256 TEXT NOT NULL CHECK (content_sha256 ~ '^[0-9a-f]{64}$'),
            review_status TEXT NOT NULL CHECK (
                review_status IN (
                    'ai_draft', 'draft', 'technical_review', 'field_review',
                    'approved', 'retired'
                )
            ),
            translation_status TEXT NOT NULL DEFAULT 'source'
                CHECK (translation_status IN ('source', 'machine_draft', 'reviewed')),
            retrieval_enabled BOOLEAN NOT NULL DEFAULT true,
            geography_json JSONB NOT NULL DEFAULT '[]'::jsonb
                CHECK (jsonb_typeof(geography_json) = 'array'),
            effective_from TIMESTAMPTZ,
            expires_at TIMESTAMPTZ,
            metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb
                CHECK (jsonb_typeof(metadata_json) = 'object'),
            PRIMARY KEY(release_id, id),
            UNIQUE(release_id, id, source_id),
            FOREIGN KEY(release_id, source_id)
                REFERENCES graph_sources(release_id, id),
            CHECK (expires_at IS NULL OR effective_from IS NULL OR expires_at > effective_from)
        );
        CREATE INDEX idx_graph_documents_release_status
            ON graph_documents(release_id, review_status, language)
            WHERE retrieval_enabled;

        CREATE TABLE graph_chunks (
            release_id TEXT NOT NULL,
            id TEXT NOT NULL,
            document_id TEXT NOT NULL,
            source_id TEXT NOT NULL,
            chunk_index INTEGER NOT NULL CHECK (chunk_index >= 0),
            section_path TEXT NOT NULL DEFAULT '',
            language TEXT NOT NULL,
            content TEXT NOT NULL CHECK (length(btrim(content)) > 0),
            normalized_content TEXT NOT NULL,
            contextualized_content TEXT NOT NULL,
            content_sha256 TEXT NOT NULL CHECK (content_sha256 ~ '^[0-9a-f]{64}$'),
            token_count INTEGER NOT NULL CHECK (token_count > 0),
            review_status TEXT NOT NULL CHECK (
                review_status IN (
                    'ai_draft', 'draft', 'technical_review', 'field_review',
                    'approved', 'retired'
                )
            ),
            risk TEXT NOT NULL DEFAULT 'medium'
                CHECK (risk IN ('low', 'medium', 'high', 'critical')),
            geography_json JSONB NOT NULL DEFAULT '[]'::jsonb
                CHECK (jsonb_typeof(geography_json) = 'array'),
            embedding_model TEXT NOT NULL,
            embedding_dimensions INTEGER NOT NULL,
            embedding vector,
            metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb
                CHECK (jsonb_typeof(metadata_json) = 'object'),
            search_vector TSVECTOR GENERATED ALWAYS AS (
                to_tsvector(
                    'simple',
                    coalesce(section_path, '') || ' ' ||
                    coalesce(normalized_content, '') || ' ' ||
                    coalesce(contextualized_content, '')
                )
            ) STORED,
            PRIMARY KEY(release_id, id),
            UNIQUE(release_id, document_id, chunk_index),
            UNIQUE(release_id, id, source_id),
            FOREIGN KEY(release_id, document_id, source_id)
                REFERENCES graph_documents(release_id, id, source_id),
            CHECK (
                embedding IS NULL
                OR vector_dims(embedding) = embedding_dimensions
            )
        );
        CREATE INDEX idx_graph_chunks_search
            ON graph_chunks USING gin(search_vector);
        CREATE INDEX idx_graph_chunks_release_filter
            ON graph_chunks(release_id, review_status, language, risk);
        CREATE INDEX idx_graph_chunks_embedding_768
            ON graph_chunks USING hnsw ((embedding::vector(768)) vector_cosine_ops)
            WHERE embedding IS NOT NULL AND embedding_dimensions = 768;
        CREATE INDEX idx_graph_chunks_embedding_1536
            ON graph_chunks USING hnsw ((embedding::vector(1536)) vector_cosine_ops)
            WHERE embedding IS NOT NULL AND embedding_dimensions = 1536;

        CREATE TABLE graph_entities (
            release_id TEXT NOT NULL REFERENCES knowledge_releases(id),
            id TEXT NOT NULL,
            entity_type TEXT NOT NULL CHECK (
                entity_type IN (
                    'crop', 'variety', 'animal', 'production_stage', 'symptom',
                    'pest', 'disease', 'practice', 'input', 'soil', 'water',
                    'climate', 'season', 'location', 'organization', 'service',
                    'market', 'regulation', 'risk', 'cost',
                    'sustainability_impact'
                )
            ),
            canonical_key TEXT NOT NULL,
            label_en TEXT,
            label_ar TEXT,
            description TEXT,
            metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb
                CHECK (jsonb_typeof(metadata_json) = 'object'),
            PRIMARY KEY(release_id, id),
            UNIQUE(release_id, entity_type, canonical_key),
            CHECK (label_en IS NOT NULL OR label_ar IS NOT NULL)
        );
        CREATE INDEX idx_graph_entities_type
            ON graph_entities(release_id, entity_type);

        CREATE TABLE graph_entity_aliases (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            release_id TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            language TEXT NOT NULL,
            script TEXT NOT NULL DEFAULT 'unknown',
            alias TEXT NOT NULL,
            normalized_alias TEXT NOT NULL,
            FOREIGN KEY(release_id, entity_id)
                REFERENCES graph_entities(release_id, id),
            UNIQUE(release_id, entity_id, language, normalized_alias)
        );
        CREATE INDEX idx_graph_alias_lookup
            ON graph_entity_aliases(release_id, normalized_alias, language);

        CREATE TABLE graph_claims (
            release_id TEXT NOT NULL REFERENCES knowledge_releases(id),
            id TEXT NOT NULL,
            claim_text TEXT NOT NULL CHECK (length(btrim(claim_text)) > 0),
            language TEXT NOT NULL,
            polarity TEXT NOT NULL DEFAULT 'positive'
                CHECK (polarity IN ('positive', 'negative', 'uncertain')),
            conditions_json JSONB NOT NULL DEFAULT '{}'::jsonb
                CHECK (jsonb_typeof(conditions_json) = 'object'),
            geography_json JSONB NOT NULL DEFAULT '[]'::jsonb
                CHECK (jsonb_typeof(geography_json) = 'array'),
            risk TEXT NOT NULL DEFAULT 'medium'
                CHECK (risk IN ('low', 'medium', 'high', 'critical')),
            review_status TEXT NOT NULL CHECK (
                review_status IN (
                    'ai_draft', 'draft', 'technical_review', 'field_review',
                    'approved', 'retired'
                )
            ),
            dynamicity TEXT NOT NULL DEFAULT 'stable'
                CHECK (dynamicity IN ('stable', 'time_sensitive')),
            effective_from TIMESTAMPTZ,
            expires_at TIMESTAMPTZ,
            content_sha256 TEXT NOT NULL CHECK (content_sha256 ~ '^[0-9a-f]{64}$'),
            metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb
                CHECK (jsonb_typeof(metadata_json) = 'object'),
            PRIMARY KEY(release_id, id),
            CHECK (expires_at IS NULL OR effective_from IS NULL OR expires_at > effective_from)
        );
        CREATE INDEX idx_graph_claims_release_status
            ON graph_claims(release_id, review_status, risk, language);

        CREATE TABLE graph_relations (
            release_id TEXT NOT NULL REFERENCES knowledge_releases(id),
            id TEXT NOT NULL,
            subject_entity_id TEXT NOT NULL,
            predicate TEXT NOT NULL CHECK (
                predicate IN (
                    'applies_to', 'requires_context', 'depends_on', 'may_cause',
                    'may_be_confused_with', 'supports_action', 'prohibits',
                    'escalates_to', 'requires_live_source', 'supported_by',
                    'supersedes', 'conflicts_with', 'related_to'
                )
            ),
            object_entity_id TEXT,
            object_text TEXT,
            polarity TEXT NOT NULL DEFAULT 'positive'
                CHECK (polarity IN ('positive', 'negative', 'uncertain')),
            qualifiers_json JSONB NOT NULL DEFAULT '{}'::jsonb
                CHECK (jsonb_typeof(qualifiers_json) = 'object'),
            geography_json JSONB NOT NULL DEFAULT '[]'::jsonb
                CHECK (jsonb_typeof(geography_json) = 'array'),
            risk TEXT NOT NULL DEFAULT 'medium'
                CHECK (risk IN ('low', 'medium', 'high', 'critical')),
            review_status TEXT NOT NULL CHECK (
                review_status IN (
                    'ai_draft', 'draft', 'technical_review', 'field_review',
                    'approved', 'retired'
                )
            ),
            effective_from TIMESTAMPTZ,
            expires_at TIMESTAMPTZ,
            metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb
                CHECK (jsonb_typeof(metadata_json) = 'object'),
            PRIMARY KEY(release_id, id),
            FOREIGN KEY(release_id, subject_entity_id)
                REFERENCES graph_entities(release_id, id),
            FOREIGN KEY(release_id, object_entity_id)
                REFERENCES graph_entities(release_id, id),
            CHECK (num_nonnulls(object_entity_id, object_text) = 1),
            CHECK (expires_at IS NULL OR effective_from IS NULL OR expires_at > effective_from)
        );
        CREATE INDEX idx_graph_relations_subject
            ON graph_relations(release_id, subject_entity_id, predicate);
        CREATE INDEX idx_graph_relations_object
            ON graph_relations(release_id, object_entity_id, predicate)
            WHERE object_entity_id IS NOT NULL;

        CREATE TABLE graph_evidence_links (
            release_id TEXT NOT NULL REFERENCES knowledge_releases(id),
            id TEXT NOT NULL,
            source_id TEXT NOT NULL,
            chunk_id TEXT NOT NULL,
            claim_id TEXT,
            relation_id TEXT,
            support_type TEXT NOT NULL DEFAULT 'supports'
                CHECK (support_type IN ('supports', 'contradicts', 'context')),
            excerpt TEXT NOT NULL CHECK (length(btrim(excerpt)) > 0),
            quote_start INTEGER,
            quote_end INTEGER,
            confidence NUMERIC(5, 4) CHECK (
                confidence IS NULL OR (confidence >= 0 AND confidence <= 1)
            ),
            metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb
                CHECK (jsonb_typeof(metadata_json) = 'object'),
            PRIMARY KEY(release_id, id),
            FOREIGN KEY(release_id, chunk_id, source_id)
                REFERENCES graph_chunks(release_id, id, source_id),
            FOREIGN KEY(release_id, claim_id)
                REFERENCES graph_claims(release_id, id),
            FOREIGN KEY(release_id, relation_id)
                REFERENCES graph_relations(release_id, id),
            CHECK (num_nonnulls(claim_id, relation_id) = 1),
            CHECK (
                (quote_start IS NULL AND quote_end IS NULL)
                OR (
                    quote_start IS NOT NULL AND quote_end IS NOT NULL
                    AND quote_start >= 0 AND quote_end > quote_start
                )
            )
        );
        CREATE INDEX idx_graph_evidence_claim
            ON graph_evidence_links(release_id, claim_id)
            WHERE claim_id IS NOT NULL;
        CREATE INDEX idx_graph_evidence_relation
            ON graph_evidence_links(release_id, relation_id)
            WHERE relation_id IS NOT NULL;
        CREATE INDEX idx_graph_evidence_chunk
            ON graph_evidence_links(release_id, chunk_id);

        CREATE TABLE project_rag_chunks (
            owner_user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            id TEXT NOT NULL,
            chunk_index INTEGER NOT NULL CHECK (chunk_index >= 0),
            language TEXT,
            content TEXT NOT NULL CHECK (length(btrim(content)) > 0),
            normalized_content TEXT NOT NULL,
            contextualized_content TEXT NOT NULL,
            content_sha256 TEXT NOT NULL CHECK (content_sha256 ~ '^[0-9a-f]{64}$'),
            embedding_model TEXT,
            embedding_dimensions INTEGER,
            embedding vector,
            metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb
                CHECK (jsonb_typeof(metadata_json) = 'object'),
            search_vector TSVECTOR GENERATED ALWAYS AS (
                to_tsvector(
                    'simple',
                    coalesce(normalized_content, '') || ' ' ||
                    coalesce(contextualized_content, '')
                )
            ) STORED,
            PRIMARY KEY(owner_user_id, id),
            UNIQUE(owner_user_id, document_id, chunk_index, embedding_model),
            CHECK (
                (embedding IS NULL AND embedding_dimensions IS NULL)
                OR (
                    embedding IS NOT NULL AND embedding_dimensions IS NOT NULL
                    AND vector_dims(embedding) = embedding_dimensions
                )
            )
        );
        CREATE INDEX idx_project_rag_chunks_scope
            ON project_rag_chunks(owner_user_id, project_id, document_id);
        CREATE INDEX idx_project_rag_chunks_search
            ON project_rag_chunks USING gin(search_vector);
        CREATE INDEX idx_project_rag_chunks_embedding_768
            ON project_rag_chunks USING hnsw ((embedding::vector(768)) vector_cosine_ops)
            WHERE embedding IS NOT NULL AND embedding_dimensions = 768;
        CREATE INDEX idx_project_rag_chunks_embedding_1536
            ON project_rag_chunks USING hnsw ((embedding::vector(1536)) vector_cosine_ops)
            WHERE embedding IS NOT NULL AND embedding_dimensions = 1536;

        CREATE FUNCTION raise_release_rows_are_mutable()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        DECLARE
            target_release_id TEXT;
            release_sealed_at TIMESTAMPTZ;
        BEGIN
            IF TG_OP = 'DELETE' THEN
                target_release_id := OLD.release_id;
            ELSE
                target_release_id := NEW.release_id;
            END IF;
            SELECT sealed_at INTO release_sealed_at
            FROM knowledge_releases
            WHERE id = target_release_id;
            IF release_sealed_at IS NOT NULL THEN
                RAISE EXCEPTION 'knowledge release % is immutable', target_release_id;
            END IF;
            IF TG_OP = 'DELETE' THEN
                RETURN OLD;
            END IF;
            RETURN NEW;
        END;
        $$;

        CREATE FUNCTION raise_release_is_immutable()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            IF OLD.sealed_at IS NOT NULL THEN
                RAISE EXCEPTION 'sealed knowledge release % is immutable', OLD.id;
            END IF;
            IF TG_OP = 'DELETE' THEN
                RETURN OLD;
            END IF;
            RETURN NEW;
        END;
        $$;

        CREATE FUNCTION raise_validate_release_seal()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        DECLARE
            should_validate BOOLEAN := false;
            source_count BIGINT;
            document_count BIGINT;
            chunk_count BIGINT;
            incomplete_runs BIGINT;
            completed_runs BIGINT;
            missing_claim_evidence BIGINT;
            missing_relation_evidence BIGINT;
            unapproved_records BIGINT;
        BEGIN
            IF NEW.state = 'ready' THEN
                IF TG_OP = 'INSERT' THEN
                    should_validate := true;
                ELSE
                    should_validate := OLD.state <> 'ready';
                END IF;
            END IF;
            IF NOT should_validate THEN
                RETURN NEW;
            END IF;
            SELECT count(*) INTO source_count
                FROM graph_sources WHERE release_id = NEW.id;
            SELECT count(*) INTO document_count
                FROM graph_documents WHERE release_id = NEW.id;
            SELECT count(*) INTO chunk_count
                FROM graph_chunks WHERE release_id = NEW.id;
            SELECT count(*) INTO incomplete_runs
                FROM graph_ingestion_runs
                WHERE release_id = NEW.id AND state <> 'completed';
            SELECT count(*) INTO completed_runs
                FROM graph_ingestion_runs
                WHERE release_id = NEW.id AND state = 'completed';
            SELECT count(*) INTO missing_claim_evidence
                FROM graph_claims claim
                WHERE claim.release_id = NEW.id AND NOT EXISTS (
                    SELECT 1 FROM graph_evidence_links evidence
                    WHERE evidence.release_id = claim.release_id
                      AND evidence.claim_id = claim.id
                );
            SELECT count(*) INTO missing_relation_evidence
                FROM graph_relations relation
                WHERE relation.release_id = NEW.id AND NOT EXISTS (
                    SELECT 1 FROM graph_evidence_links evidence
                    WHERE evidence.release_id = relation.release_id
                      AND evidence.relation_id = relation.id
                );
            IF source_count < 1 OR document_count < 1 OR chunk_count < 1
               OR incomplete_runs > 0 OR completed_runs < 1
               OR missing_claim_evidence > 0 OR missing_relation_evidence > 0 THEN
                RAISE EXCEPTION 'knowledge release % failed seal integrity checks', NEW.id;
            END IF;
            IF NEW.review_policy = 'approved_only' THEN
                SELECT
                    (SELECT count(*) FROM graph_documents
                        WHERE release_id = NEW.id AND review_status <> 'approved')
                    + (SELECT count(*) FROM graph_chunks
                        WHERE release_id = NEW.id AND review_status <> 'approved')
                    + (SELECT count(*) FROM graph_claims
                        WHERE release_id = NEW.id AND review_status <> 'approved')
                    + (SELECT count(*) FROM graph_relations
                        WHERE release_id = NEW.id AND review_status <> 'approved')
                INTO unapproved_records;
                IF unapproved_records > 0 THEN
                    RAISE EXCEPTION
                        'approved-only release % contains unapproved records', NEW.id;
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$;

        CREATE FUNCTION raise_validate_active_release()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        DECLARE
            release_state TEXT;
            release_scope TEXT;
            release_policy TEXT;
        BEGIN
            SELECT state, publication_scope, review_policy
            INTO release_state, release_scope, release_policy
            FROM knowledge_releases WHERE id = NEW.release_id;
            IF release_state <> 'ready' THEN
                RAISE EXCEPTION 'active knowledge release must be sealed and ready';
            END IF;
            IF NEW.deployment_scope = 'production'
               AND (release_scope <> 'production' OR release_policy <> 'approved_only') THEN
                RAISE EXCEPTION
                    'production requires an approved-only production release';
            END IF;
            IF NEW.deployment_scope = 'pilot' AND release_scope = 'internal' THEN
                RAISE EXCEPTION 'internal releases cannot be activated for pilot';
            END IF;
            RETURN NEW;
        END;
        $$;

        CREATE TRIGGER knowledge_release_immutable
            BEFORE UPDATE OR DELETE ON knowledge_releases
            FOR EACH ROW EXECUTE FUNCTION raise_release_is_immutable();
        CREATE TRIGGER knowledge_release_seal_integrity
            BEFORE INSERT OR UPDATE ON knowledge_releases
            FOR EACH ROW EXECUTE FUNCTION raise_validate_release_seal();
        CREATE TRIGGER active_release_integrity
            BEFORE INSERT OR UPDATE ON active_knowledge_releases
            FOR EACH ROW EXECUTE FUNCTION raise_validate_active_release();

        CREATE TRIGGER graph_sources_release_mutable
            BEFORE INSERT OR UPDATE OR DELETE ON graph_sources
            FOR EACH ROW EXECUTE FUNCTION raise_release_rows_are_mutable();
        CREATE TRIGGER graph_documents_release_mutable
            BEFORE INSERT OR UPDATE OR DELETE ON graph_documents
            FOR EACH ROW EXECUTE FUNCTION raise_release_rows_are_mutable();
        CREATE TRIGGER graph_chunks_release_mutable
            BEFORE INSERT OR UPDATE OR DELETE ON graph_chunks
            FOR EACH ROW EXECUTE FUNCTION raise_release_rows_are_mutable();
        CREATE TRIGGER graph_entities_release_mutable
            BEFORE INSERT OR UPDATE OR DELETE ON graph_entities
            FOR EACH ROW EXECUTE FUNCTION raise_release_rows_are_mutable();
        CREATE TRIGGER graph_aliases_release_mutable
            BEFORE INSERT OR UPDATE OR DELETE ON graph_entity_aliases
            FOR EACH ROW EXECUTE FUNCTION raise_release_rows_are_mutable();
        CREATE TRIGGER graph_claims_release_mutable
            BEFORE INSERT OR UPDATE OR DELETE ON graph_claims
            FOR EACH ROW EXECUTE FUNCTION raise_release_rows_are_mutable();
        CREATE TRIGGER graph_relations_release_mutable
            BEFORE INSERT OR UPDATE OR DELETE ON graph_relations
            FOR EACH ROW EXECUTE FUNCTION raise_release_rows_are_mutable();
        CREATE TRIGGER graph_evidence_release_mutable
            BEFORE INSERT OR UPDATE OR DELETE ON graph_evidence_links
            FOR EACH ROW EXECUTE FUNCTION raise_release_rows_are_mutable();
        CREATE TRIGGER graph_runs_release_mutable
            BEFORE INSERT OR UPDATE OR DELETE ON graph_ingestion_runs
            FOR EACH ROW EXECUTE FUNCTION raise_release_rows_are_mutable();

        CREATE FUNCTION raise_validate_chunk_embedding()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        DECLARE
            release_model TEXT;
            release_dimensions INTEGER;
        BEGIN
            SELECT embedding_model, embedding_dimensions
            INTO release_model, release_dimensions
            FROM knowledge_releases
            WHERE id = NEW.release_id;
            IF NEW.embedding_model <> release_model
               OR NEW.embedding_dimensions <> release_dimensions THEN
                RAISE EXCEPTION 'chunk embedding configuration differs from release %',
                    NEW.release_id;
            END IF;
            RETURN NEW;
        END;
        $$;
        CREATE TRIGGER graph_chunk_embedding_matches_release
            BEFORE INSERT OR UPDATE ON graph_chunks
            FOR EACH ROW EXECUTE FUNCTION raise_validate_chunk_embedding();

        CREATE FUNCTION raise_validate_project_chunk_scope()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM documents d
                WHERE d.id = NEW.document_id
                  AND d.owner_user_id = NEW.owner_user_id
                  AND d.project_id = NEW.project_id
            ) THEN
                RAISE EXCEPTION 'project chunk scope does not match its document';
            END IF;
            RETURN NEW;
        END;
        $$;
        CREATE TRIGGER project_chunk_scope_matches_document
            BEFORE INSERT OR UPDATE ON project_rag_chunks
            FOR EACH ROW EXECUTE FUNCTION raise_validate_project_chunk_scope();

        CREATE FUNCTION raise_relation_requires_evidence()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM graph_evidence_links evidence
                WHERE evidence.release_id = NEW.release_id
                  AND evidence.relation_id = NEW.id
            ) THEN
                RAISE EXCEPTION 'graph relation % requires passage evidence', NEW.id;
            END IF;
            RETURN NULL;
        END;
        $$;
        CREATE CONSTRAINT TRIGGER graph_relation_has_evidence
            AFTER INSERT OR UPDATE ON graph_relations
            DEFERRABLE INITIALLY DEFERRED
            FOR EACH ROW EXECUTE FUNCTION raise_relation_requires_evidence();

        CREATE FUNCTION raise_claim_requires_evidence()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM graph_evidence_links evidence
                WHERE evidence.release_id = NEW.release_id
                  AND evidence.claim_id = NEW.id
            ) THEN
                RAISE EXCEPTION 'graph claim % requires passage evidence', NEW.id;
            END IF;
            RETURN NULL;
        END;
        $$;
        CREATE CONSTRAINT TRIGGER graph_claim_has_evidence
            AFTER INSERT OR UPDATE ON graph_claims
            DEFERRABLE INITIALLY DEFERRED
            FOR EACH ROW EXECUTE FUNCTION raise_claim_requires_evidence();

        CREATE OR REPLACE FUNCTION hybrid_search_knowledge_v2(
            p_release_id TEXT,
            p_query_text TEXT,
            p_query_embedding vector DEFAULT NULL,
            p_embedding_model TEXT DEFAULT NULL,
            p_embedding_dimensions INTEGER DEFAULT NULL,
            p_match_count INTEGER DEFAULT 10,
            p_required_statuses TEXT[] DEFAULT ARRAY['approved']::TEXT[]
        )
        RETURNS TABLE (
            evidence_id TEXT,
            chunk_id TEXT,
            document_id TEXT,
            source_id TEXT,
            title TEXT,
            content TEXT,
            language TEXT,
            review_status TEXT,
            risk TEXT,
            geography_json JSONB,
            lexical_rank BIGINT,
            semantic_rank BIGINT,
            score DOUBLE PRECISION
        )
        LANGUAGE sql
        STABLE
        AS $$
        WITH eligible AS (
            SELECT chunk.*
            FROM graph_chunks chunk
            JOIN graph_documents document
              ON document.release_id = chunk.release_id
             AND document.id = chunk.document_id
            WHERE chunk.release_id = p_release_id
              AND chunk.review_status = ANY(p_required_statuses)
              AND document.retrieval_enabled
              AND (document.effective_from IS NULL OR document.effective_from <= now())
              AND (document.expires_at IS NULL OR document.expires_at > now())
        ),
        lexical AS (
            SELECT eligible.id,
                   row_number() OVER (
                       ORDER BY ts_rank_cd(
                           eligible.search_vector,
                           websearch_to_tsquery('simple', p_query_text)
                       ) DESC,
                       eligible.id
                   ) AS rank
            FROM eligible
            WHERE btrim(p_query_text) <> ''
              AND eligible.search_vector @@ websearch_to_tsquery('simple', p_query_text)
            ORDER BY rank
            LIMIT LEAST(GREATEST(p_match_count, 1) * 4, 100)
        ),
        semantic AS (
            SELECT eligible.id,
                   row_number() OVER (
                       ORDER BY eligible.embedding <=> p_query_embedding, eligible.id
                   ) AS rank
            FROM eligible
            WHERE p_query_embedding IS NOT NULL
              AND p_embedding_model IS NOT NULL
              AND p_embedding_dimensions IS NOT NULL
              AND eligible.embedding IS NOT NULL
              AND eligible.embedding_model = p_embedding_model
              AND eligible.embedding_dimensions = p_embedding_dimensions
              AND vector_dims(p_query_embedding) = p_embedding_dimensions
            ORDER BY rank
            LIMIT LEAST(GREATEST(p_match_count, 1) * 4, 100)
        ),
        fused AS (
            SELECT coalesce(lexical.id, semantic.id) AS id,
                   lexical.rank AS lexical_rank,
                   semantic.rank AS semantic_rank,
                   coalesce(1.0 / (60 + lexical.rank), 0.0)
                   + coalesce(1.0 / (60 + semantic.rank), 0.0) AS score
            FROM lexical
            FULL OUTER JOIN semantic ON semantic.id = lexical.id
        )
        SELECT 'chunk:' || eligible.release_id || ':' || eligible.id,
               eligible.id,
               eligible.document_id,
               eligible.source_id,
               document.title,
               eligible.content,
               eligible.language,
               eligible.review_status,
               eligible.risk,
               eligible.geography_json,
               fused.lexical_rank,
               fused.semantic_rank,
               fused.score
        FROM fused
        JOIN eligible ON eligible.id = fused.id
        JOIN graph_documents document
          ON document.release_id = eligible.release_id
         AND document.id = eligible.document_id
        ORDER BY fused.score DESC, eligible.id
        LIMIT LEAST(GREATEST(p_match_count, 1), 50);
        $$;
        """
    )


def downgrade() -> None:
    op.execute(
        r"""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM knowledge_releases LIMIT 1)
               OR EXISTS (SELECT 1 FROM project_rag_chunks LIMIT 1) THEN
                RAISE EXCEPTION
                    'refusing GraphRAG downgrade while release or project data exists';
            END IF;
        END;
        $$;

        DROP FUNCTION IF EXISTS hybrid_search_knowledge_v2(
            TEXT, TEXT, vector, TEXT, INTEGER, INTEGER, TEXT[]
        );
        DROP TRIGGER IF EXISTS graph_claim_has_evidence ON graph_claims;
        DROP TRIGGER IF EXISTS graph_relation_has_evidence ON graph_relations;
        DROP TRIGGER IF EXISTS active_release_integrity ON active_knowledge_releases;
        DROP TRIGGER IF EXISTS knowledge_release_seal_integrity ON knowledge_releases;
        DROP TRIGGER IF EXISTS project_chunk_scope_matches_document ON project_rag_chunks;
        DROP TRIGGER IF EXISTS graph_chunk_embedding_matches_release ON graph_chunks;
        DROP TRIGGER IF EXISTS graph_runs_release_mutable ON graph_ingestion_runs;
        DROP TRIGGER IF EXISTS graph_evidence_release_mutable ON graph_evidence_links;
        DROP TRIGGER IF EXISTS graph_relations_release_mutable ON graph_relations;
        DROP TRIGGER IF EXISTS graph_claims_release_mutable ON graph_claims;
        DROP TRIGGER IF EXISTS graph_aliases_release_mutable ON graph_entity_aliases;
        DROP TRIGGER IF EXISTS graph_entities_release_mutable ON graph_entities;
        DROP TRIGGER IF EXISTS graph_chunks_release_mutable ON graph_chunks;
        DROP TRIGGER IF EXISTS graph_documents_release_mutable ON graph_documents;
        DROP TRIGGER IF EXISTS graph_sources_release_mutable ON graph_sources;
        DROP TRIGGER IF EXISTS knowledge_release_immutable ON knowledge_releases;

        DROP FUNCTION IF EXISTS raise_claim_requires_evidence();
        DROP FUNCTION IF EXISTS raise_relation_requires_evidence();
        DROP FUNCTION IF EXISTS raise_validate_project_chunk_scope();
        DROP FUNCTION IF EXISTS raise_validate_chunk_embedding();
        DROP FUNCTION IF EXISTS raise_validate_active_release();
        DROP FUNCTION IF EXISTS raise_validate_release_seal();
        DROP FUNCTION IF EXISTS raise_release_is_immutable();
        DROP FUNCTION IF EXISTS raise_release_rows_are_mutable();

        DROP TABLE IF EXISTS project_rag_chunks;
        DROP TABLE IF EXISTS graph_evidence_links;
        DROP TABLE IF EXISTS graph_relations;
        DROP TABLE IF EXISTS graph_claims;
        DROP TABLE IF EXISTS graph_entity_aliases;
        DROP TABLE IF EXISTS graph_entities;
        DROP TABLE IF EXISTS graph_chunks;
        DROP TABLE IF EXISTS graph_documents;
        DROP TABLE IF EXISTS graph_sources;
        DROP TABLE IF EXISTS graph_ingestion_runs;
        DROP TABLE IF EXISTS knowledge_release_activations;
        DROP TABLE IF EXISTS active_knowledge_releases;
        DROP TABLE IF EXISTS knowledge_releases;
        """
    )
