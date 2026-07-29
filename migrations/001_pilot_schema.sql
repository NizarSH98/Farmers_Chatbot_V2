CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    issuer TEXT NOT NULL,
    subject TEXT NOT NULL,
    email TEXT,
    name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',
    consent_version TEXT,
    consent_at TEXT,
    default_mode TEXT NOT NULL DEFAULT 'standard',
    created_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    UNIQUE (issuer, subject)
);

CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    instructions TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id TEXT REFERENCES projects(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    channel TEXT NOT NULL DEFAULT 'web',
    archived INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_conversations_owner_updated
    ON conversations(owner_user_id, updated_at);

CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    language TEXT,
    mode TEXT,
    model TEXT,
    status TEXT NOT NULL DEFAULT 'complete',
    citations_json TEXT NOT NULL DEFAULT '[]',
    tools_json TEXT NOT NULL DEFAULT '[]',
    artifacts_json TEXT NOT NULL DEFAULT '[]',
    attachments_json TEXT NOT NULL DEFAULT '[]',
    warning TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_messages_conversation
    ON messages(conversation_id, created_at);

CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    status TEXT NOT NULL,
    error_message TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS document_chunks (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    text_content TEXT NOT NULL,
    UNIQUE(document_id, chunk_index)
);

CREATE TABLE IF NOT EXISTS artifacts (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
    conversation_id TEXT REFERENCES conversations(id) ON DELETE CASCADE,
    artifact_type TEXT NOT NULL,
    filename TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS feedback (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    occurred_at TEXT NOT NULL,
    user_id TEXT REFERENCES users(id) ON DELETE SET NULL,
    message_id TEXT REFERENCES messages(id) ON DELETE SET NULL,
    category TEXT NOT NULL,
    rating INTEGER,
    comment TEXT NOT NULL,
    language TEXT,
    consent INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'new',
    priority TEXT,
    release_version TEXT,
    verification_note TEXT
);

CREATE TABLE IF NOT EXISTS query_events (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    occurred_at TEXT NOT NULL,
    day_utc TEXT NOT NULL,
    user_id TEXT REFERENCES users(id) ON DELETE SET NULL,
    mode TEXT NOT NULL,
    language TEXT,
    duration_ms INTEGER,
    success INTEGER,
    error_type TEXT,
    trusted_searches INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_pilot_query_day ON query_events(day_utc);
CREATE INDEX IF NOT EXISTS idx_pilot_query_user
    ON query_events(user_id, occurred_at);

CREATE TABLE IF NOT EXISTS whatsapp_events (
    message_id TEXT PRIMARY KEY,
    identity_hash TEXT NOT NULL,
    status TEXT NOT NULL,
    error_type TEXT,
    received_at TEXT NOT NULL,
    completed_at TEXT
);
