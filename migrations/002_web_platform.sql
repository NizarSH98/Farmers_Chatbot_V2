CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE users ADD COLUMN IF NOT EXISTS auth_user_id TEXT;
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_auth_user_id
    ON users(auth_user_id) WHERE auth_user_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS uploads (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    storage_path TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'ready',
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_uploads_owner_created
    ON uploads(owner_user_id, created_at);

CREATE TABLE IF NOT EXISTS assistant_turns (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    user_message_id TEXT REFERENCES messages(id) ON DELETE SET NULL,
    assistant_message_id TEXT REFERENCES messages(id) ON DELETE SET NULL,
    status TEXT NOT NULL,
    clarification_count INTEGER NOT NULL DEFAULT 0,
    analysis_json TEXT NOT NULL DEFAULT '{}',
    error_type TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_assistant_turns_conversation
    ON assistant_turns(conversation_id, created_at);

ALTER TABLE query_events ADD COLUMN IF NOT EXISTS request_id TEXT;
ALTER TABLE query_events ADD COLUMN IF NOT EXISTS ttft_ms INTEGER;
ALTER TABLE query_events ADD COLUMN IF NOT EXISTS stage_durations_json TEXT
    NOT NULL DEFAULT '{}';
ALTER TABLE query_events ADD COLUMN IF NOT EXISTS prompt_tokens INTEGER;
ALTER TABLE query_events ADD COLUMN IF NOT EXISTS completion_tokens INTEGER;
ALTER TABLE query_events ADD COLUMN IF NOT EXISTS estimated_cost_usd NUMERIC(12, 6);

CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    document_version TEXT NOT NULL,
    page_reference TEXT,
    section TEXT,
    language TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    authority TEXT NOT NULL,
    review_status TEXT NOT NULL DEFAULT 'staging',
    geography_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    embedding_model TEXT,
    embedding vector(1536),
    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(content, ''))
    ) STORED,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_search
    ON knowledge_chunks USING gin(search_vector);
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_embedding
    ON knowledge_chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_status_language
    ON knowledge_chunks(review_status, language);

CREATE OR REPLACE FUNCTION hybrid_search_raise(
    query_text TEXT,
    query_embedding vector(1536),
    match_count INTEGER DEFAULT 10,
    required_status TEXT DEFAULT 'approved'
)
RETURNS TABLE (
    id TEXT,
    source_id TEXT,
    title TEXT,
    content TEXT,
    language TEXT,
    page_reference TEXT,
    authority TEXT,
    review_status TEXT,
    score DOUBLE PRECISION
)
LANGUAGE sql
STABLE
AS $$
WITH semantic AS (
    SELECT kc.id,
           row_number() OVER (
               ORDER BY kc.embedding <=> query_embedding
           ) AS rank
    FROM knowledge_chunks kc
    WHERE kc.review_status = required_status
      AND kc.embedding IS NOT NULL
    ORDER BY kc.embedding <=> query_embedding
    LIMIT LEAST(match_count * 3, 60)
),
lexical AS (
    SELECT kc.id,
           row_number() OVER (
               ORDER BY ts_rank_cd(
                   kc.search_vector,
                   websearch_to_tsquery('simple', query_text)
               ) DESC
           ) AS rank
    FROM knowledge_chunks kc
    WHERE kc.review_status = required_status
      AND kc.search_vector @@ websearch_to_tsquery('simple', query_text)
    ORDER BY ts_rank_cd(
        kc.search_vector,
        websearch_to_tsquery('simple', query_text)
    ) DESC
    LIMIT LEAST(match_count * 3, 60)
),
fused AS (
    SELECT coalesce(semantic.id, lexical.id) AS id,
           coalesce(1.0 / (60 + semantic.rank), 0.0)
           + coalesce(1.0 / (60 + lexical.rank), 0.0) AS score
    FROM semantic
    FULL OUTER JOIN lexical ON semantic.id = lexical.id
)
SELECT kc.id,
       kc.source_id,
       kc.title,
       kc.content,
       kc.language,
       kc.page_reference,
       kc.authority,
       kc.review_status,
       fused.score
FROM fused
JOIN knowledge_chunks kc ON kc.id = fused.id
ORDER BY fused.score DESC
LIMIT match_count;
$$;
