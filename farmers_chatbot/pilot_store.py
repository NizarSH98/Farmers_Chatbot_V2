"""Persistent pilot workspace store with SQLite and PostgreSQL backends."""

from __future__ import annotations

import hashlib
import hmac
import json
import sqlite3
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .auth import UserIdentity
from .config import (
    CONSENT_VERSION,
    DATABASE_URL,
    LOCAL_PILOT_DB_PATH,
    MAX_ARTIFACTS_PER_USER_DAY,
    MAX_DEEP_QUERIES_PER_USER_DAY,
    MAX_PILOT_QUERIES_PER_DAY,
    MAX_QUERIES_PER_USER_DAY,
    PILOT_COOLDOWN_SECONDS,
)


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True)
class PilotRateLimit:
    allowed: bool
    message: str | None
    remaining_user: int


class PilotStore:
    """Application persistence that fails closed on ownership checks."""

    def __init__(
        self,
        database_url: str = DATABASE_URL,
        sqlite_path: str | Path = LOCAL_PILOT_DB_PATH,
    ) -> None:
        self.database_url = database_url.strip()
        self.sqlite_path = Path(sqlite_path)
        self.is_postgres = self.database_url.startswith(
            ("postgres://", "postgresql://")
        )
        if not self.is_postgres:
            self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @contextmanager
    def _connect(self) -> Iterator[Any]:
        if self.is_postgres:
            try:
                import psycopg
                from psycopg.rows import dict_row
            except ImportError as exc:  # pragma: no cover - deployment dependency
                raise RuntimeError("PostgreSQL support requires psycopg") from exc
            with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
                yield connection
            return

        connection = sqlite3.connect(self.sqlite_path, timeout=15)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def _sql(self, statement: str) -> str:
        return statement.replace("?", "%s") if self.is_postgres else statement

    def _initialize(self) -> None:
        if self.is_postgres:
            migration = (
                Path(__file__).resolve().parents[1]
                / "migrations"
                / "001_pilot_schema.sql"
            )
            with self._connect() as connection:
                connection.execute(migration.read_text(encoding="utf-8"))
            return

        with self._connect() as connection:
            connection.executescript(
                """
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
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                CREATE INDEX IF NOT EXISTS idx_pilot_query_day
                    ON query_events(day_utc);
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
                """
            )

    def upsert_user(self, identity: UserIdentity) -> dict[str, Any]:
        now = utc_now()
        role = "admin" if identity.is_admin else "user"
        with self._connect() as connection:
            row = connection.execute(
                self._sql("SELECT * FROM users WHERE issuer = ? AND subject = ?"),
                (identity.issuer, identity.subject),
            ).fetchone()
            if row:
                connection.execute(
                    self._sql(
                        """
                        UPDATE users
                        SET email = ?, name = ?, role = ?, last_seen_at = ?
                        WHERE id = ?
                        """
                    ),
                    (identity.email or None, identity.name, role, now, row["id"]),
                )
                user_id = str(row["id"])
            else:
                user_id = str(uuid.uuid4())
                connection.execute(
                    self._sql(
                        """
                        INSERT INTO users
                            (id, issuer, subject, email, name, role,
                             created_at, last_seen_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """
                    ),
                    (
                        user_id,
                        identity.issuer,
                        identity.subject,
                        identity.email or None,
                        identity.name,
                        role,
                        now,
                        now,
                    ),
                )
        return self.get_user(user_id)

    def upsert_whatsapp_user(self, identity_hash: str) -> dict[str, Any]:
        identity = UserIdentity(
            user_id="",
            issuer="whatsapp-cloud-api",
            subject=identity_hash,
            email="",
            name="WhatsApp pilot user",
            is_admin=False,
        )
        return self.upsert_user(identity)

    def get_user(self, user_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                self._sql("SELECT * FROM users WHERE id = ?"),
                (user_id,),
            ).fetchone()
        if not row:
            raise ValueError("User not found")
        return dict(row)

    def has_current_consent(self, user_id: str) -> bool:
        user = self.get_user(user_id)
        return bool(
            user.get("consent_at") and user.get("consent_version") == CONSENT_VERSION
        )

    def accept_consent(self, user_id: str) -> None:
        with self._connect() as connection:
            connection.execute(
                self._sql(
                    "UPDATE users SET consent_version = ?, consent_at = ? WHERE id = ?"
                ),
                (CONSENT_VERSION, utc_now(), user_id),
            )

    def update_user_preferences(
        self,
        user_id: str,
        *,
        default_mode: str,
    ) -> None:
        if default_mode not in {"quick", "standard", "deep", "source_only"}:
            raise ValueError("Unknown response mode")
        with self._connect() as connection:
            cursor = connection.execute(
                self._sql("UPDATE users SET default_mode = ? WHERE id = ?"),
                (default_mode, user_id),
            )
            if cursor.rowcount != 1:
                raise ValueError("User not found")

    def create_project(
        self,
        owner_user_id: str,
        name: str,
        instructions: str = "",
    ) -> str:
        cleaned = " ".join(name.split()).strip()
        if not cleaned or len(cleaned) > 100:
            raise ValueError("Project name must be 1–100 characters")
        project_id = str(uuid.uuid4())
        now = utc_now()
        with self._connect() as connection:
            connection.execute(
                self._sql(
                    """
                    INSERT INTO projects
                        (id, owner_user_id, name, instructions, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """
                ),
                (
                    project_id,
                    owner_user_id,
                    cleaned,
                    instructions.strip()[:5000],
                    now,
                    now,
                ),
            )
        return project_id

    def list_projects(self, owner_user_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                self._sql(
                    """
                    SELECT * FROM projects
                    WHERE owner_user_id = ?
                    ORDER BY updated_at DESC
                    """
                ),
                (owner_user_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_project(self, owner_user_id: str, project_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                self._sql("SELECT * FROM projects WHERE id = ? AND owner_user_id = ?"),
                (project_id, owner_user_id),
            ).fetchone()
        if not row:
            raise ValueError("Project not found")
        return dict(row)

    def update_project(
        self,
        owner_user_id: str,
        project_id: str,
        *,
        name: str,
        instructions: str,
    ) -> None:
        cleaned = " ".join(name.split()).strip()
        if not cleaned or len(cleaned) > 100:
            raise ValueError("Project name must be 1–100 characters")
        with self._connect() as connection:
            cursor = connection.execute(
                self._sql(
                    """
                    UPDATE projects
                    SET name = ?, instructions = ?, updated_at = ?
                    WHERE id = ? AND owner_user_id = ?
                    """
                ),
                (
                    cleaned,
                    instructions.strip()[:5000],
                    utc_now(),
                    project_id,
                    owner_user_id,
                ),
            )
            if cursor.rowcount != 1:
                raise ValueError("Project not found")

    def delete_project(self, owner_user_id: str, project_id: str) -> list[str]:
        documents = self.list_documents(owner_user_id, project_id)
        artifacts = self.list_artifacts(owner_user_id, project_id=project_id)
        paths = [item["storage_path"] for item in [*documents, *artifacts]]
        with self._connect() as connection:
            cursor = connection.execute(
                self._sql("DELETE FROM projects WHERE id = ? AND owner_user_id = ?"),
                (project_id, owner_user_id),
            )
            if cursor.rowcount != 1:
                raise ValueError("Project not found")
        return paths

    def create_conversation(
        self,
        owner_user_id: str,
        title: str = "New conversation",
        *,
        project_id: str | None = None,
        channel: str = "web",
    ) -> str:
        if project_id:
            self.get_project(owner_user_id, project_id)
        conversation_id = str(uuid.uuid4())
        now = utc_now()
        with self._connect() as connection:
            connection.execute(
                self._sql(
                    """
                    INSERT INTO conversations
                        (id, owner_user_id, project_id, title, channel,
                         created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """
                ),
                (
                    conversation_id,
                    owner_user_id,
                    project_id,
                    title.strip()[:120] or "New conversation",
                    channel,
                    now,
                    now,
                ),
            )
        return conversation_id

    def get_or_create_channel_conversation(
        self,
        owner_user_id: str,
        channel: str,
    ) -> str:
        with self._connect() as connection:
            row = connection.execute(
                self._sql(
                    """
                    SELECT id FROM conversations
                    WHERE owner_user_id = ? AND channel = ? AND archived = 0
                    ORDER BY updated_at DESC LIMIT 1
                    """
                ),
                (owner_user_id, channel),
            ).fetchone()
        if row:
            return str(row["id"])
        return self.create_conversation(
            owner_user_id,
            f"{channel.title()} conversation",
            channel=channel,
        )

    def list_conversations(
        self,
        owner_user_id: str,
        *,
        project_id: str | None = None,
        search: str = "",
        include_archived: bool = False,
    ) -> list[dict[str, Any]]:
        clauses = ["owner_user_id = ?"]
        parameters: list[Any] = [owner_user_id]
        if not include_archived:
            clauses.append("archived = 0")
        if project_id:
            clauses.append("project_id = ?")
            parameters.append(project_id)
        if search.strip():
            clauses.append("LOWER(title) LIKE ?")
            parameters.append(f"%{search.strip().lower()}%")
        query = (
            "SELECT * FROM conversations WHERE "
            + " AND ".join(clauses)
            + " ORDER BY updated_at DESC LIMIT 100"
        )
        with self._connect() as connection:
            rows = connection.execute(self._sql(query), parameters).fetchall()
        return [dict(row) for row in rows]

    def get_conversation(
        self,
        owner_user_id: str,
        conversation_id: str,
    ) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                self._sql(
                    """
                    SELECT * FROM conversations
                    WHERE id = ? AND owner_user_id = ?
                    """
                ),
                (conversation_id, owner_user_id),
            ).fetchone()
        if not row:
            raise ValueError("Conversation not found")
        return dict(row)

    def archive_conversation(
        self,
        owner_user_id: str,
        conversation_id: str,
    ) -> None:
        with self._connect() as connection:
            cursor = connection.execute(
                self._sql(
                    """
                    UPDATE conversations
                    SET archived = 1, updated_at = ?
                    WHERE id = ? AND owner_user_id = ?
                    """
                ),
                (utc_now(), conversation_id, owner_user_id),
            )
            if cursor.rowcount != 1:
                raise ValueError("Conversation not found")

    def rename_conversation(
        self,
        owner_user_id: str,
        conversation_id: str,
        title: str,
    ) -> None:
        cleaned = " ".join(title.split()).strip()[:120]
        if not cleaned:
            raise ValueError("Conversation title cannot be empty")
        with self._connect() as connection:
            cursor = connection.execute(
                self._sql(
                    """
                    UPDATE conversations SET title = ?, updated_at = ?
                    WHERE id = ? AND owner_user_id = ?
                    """
                ),
                (cleaned, utc_now(), conversation_id, owner_user_id),
            )
            if cursor.rowcount != 1:
                raise ValueError("Conversation not found")

    def delete_conversation(
        self, owner_user_id: str, conversation_id: str
    ) -> list[str]:
        artifacts = self.list_artifacts(
            owner_user_id,
            conversation_id=conversation_id,
        )
        paths = [artifact["storage_path"] for artifact in artifacts]
        for message in self.list_messages(owner_user_id, conversation_id):
            for attachment in message.get("attachments", []):
                storage_path = attachment.get("storage_path")
                if storage_path:
                    paths.append(str(storage_path))
        with self._connect() as connection:
            cursor = connection.execute(
                self._sql(
                    "DELETE FROM conversations WHERE id = ? AND owner_user_id = ?"
                ),
                (conversation_id, owner_user_id),
            )
            if cursor.rowcount != 1:
                raise ValueError("Conversation not found")
        return list(dict.fromkeys(paths))

    def add_message(
        self,
        owner_user_id: str,
        conversation_id: str,
        *,
        role: str,
        content: str,
        language: str | None = None,
        mode: str | None = None,
        model: str | None = None,
        status: str = "complete",
        citations: list[dict[str, Any]] | None = None,
        tools: list[str] | None = None,
        artifact_ids: list[str] | None = None,
        attachments: list[dict[str, Any]] | None = None,
        warning: str | None = None,
    ) -> str:
        if role not in {"user", "assistant", "system"}:
            raise ValueError("Invalid message role")
        self.get_conversation(owner_user_id, conversation_id)
        message_id = str(uuid.uuid4())
        now = utc_now()
        with self._connect() as connection:
            connection.execute(
                self._sql(
                    """
                    INSERT INTO messages
                        (id, conversation_id, role, content, language, mode, model,
                         status, citations_json, tools_json, artifacts_json,
                         attachments_json, warning, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                ),
                (
                    message_id,
                    conversation_id,
                    role,
                    content[:100000],
                    language,
                    mode,
                    model,
                    status,
                    json.dumps(citations or [], ensure_ascii=False),
                    json.dumps(tools or [], ensure_ascii=False),
                    json.dumps(artifact_ids or [], ensure_ascii=False),
                    json.dumps(attachments or [], ensure_ascii=False),
                    warning,
                    now,
                ),
            )
            connection.execute(
                self._sql("UPDATE conversations SET updated_at = ? WHERE id = ?"),
                (now, conversation_id),
            )
        return message_id

    def list_messages(
        self,
        owner_user_id: str,
        conversation_id: str,
        *,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        self.get_conversation(owner_user_id, conversation_id)
        with self._connect() as connection:
            rows = connection.execute(
                self._sql(
                    """
                    SELECT * FROM messages
                    WHERE conversation_id = ?
                    ORDER BY created_at ASC LIMIT ?
                    """
                ),
                (conversation_id, max(1, min(int(limit), 500))),
            ).fetchall()
        messages = []
        for row in rows:
            item = dict(row)
            for source, target in (
                ("citations_json", "citations"),
                ("tools_json", "tools"),
                ("artifacts_json", "artifact_ids"),
                ("attachments_json", "attachments"),
            ):
                item[target] = json.loads(item.pop(source) or "[]")
            messages.append(item)
        return messages

    def document_count(self, owner_user_id: str, project_id: str) -> int:
        self.get_project(owner_user_id, project_id)
        with self._connect() as connection:
            row = connection.execute(
                self._sql(
                    """
                    SELECT COUNT(*) AS count FROM documents
                    WHERE owner_user_id = ? AND project_id = ?
                    """
                ),
                (owner_user_id, project_id),
            ).fetchone()
        return int(row["count"])

    def add_document(
        self,
        owner_user_id: str,
        project_id: str,
        *,
        filename: str,
        mime_type: str,
        storage_path: str,
        sha256: str,
        size_bytes: int,
        chunks: list[str],
    ) -> str:
        self.get_project(owner_user_id, project_id)
        document_id = str(uuid.uuid4())
        with self._connect() as connection:
            connection.execute(
                self._sql(
                    """
                    INSERT INTO documents
                        (id, owner_user_id, project_id, filename, mime_type,
                         storage_path, sha256, size_bytes, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'ready', ?)
                    """
                ),
                (
                    document_id,
                    owner_user_id,
                    project_id,
                    filename[:255],
                    mime_type,
                    storage_path,
                    sha256,
                    int(size_bytes),
                    utc_now(),
                ),
            )
            for index, text in enumerate(chunks):
                connection.execute(
                    self._sql(
                        """
                        INSERT INTO document_chunks
                            (id, document_id, chunk_index, text_content)
                        VALUES (?, ?, ?, ?)
                        """
                    ),
                    (str(uuid.uuid4()), document_id, index, text),
                )
        return document_id

    def list_documents(
        self,
        owner_user_id: str,
        project_id: str,
    ) -> list[dict[str, Any]]:
        self.get_project(owner_user_id, project_id)
        with self._connect() as connection:
            rows = connection.execute(
                self._sql(
                    """
                    SELECT * FROM documents
                    WHERE owner_user_id = ? AND project_id = ?
                    ORDER BY created_at DESC
                    """
                ),
                (owner_user_id, project_id),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_project_chunks(
        self,
        owner_user_id: str,
        project_id: str,
    ) -> list[dict[str, Any]]:
        self.get_project(owner_user_id, project_id)
        with self._connect() as connection:
            rows = connection.execute(
                self._sql(
                    """
                    SELECT c.id, c.chunk_index, c.text_content,
                           d.id AS document_id, d.filename
                    FROM document_chunks c
                    JOIN documents d ON d.id = c.document_id
                    WHERE d.owner_user_id = ? AND d.project_id = ?
                          AND d.status = 'ready'
                    ORDER BY d.created_at, c.chunk_index
                    """
                ),
                (owner_user_id, project_id),
            ).fetchall()
        return [dict(row) for row in rows]

    def delete_document(
        self,
        owner_user_id: str,
        project_id: str,
        document_id: str,
    ) -> str:
        with self._connect() as connection:
            row = connection.execute(
                self._sql(
                    """
                    SELECT storage_path FROM documents
                    WHERE id = ? AND project_id = ? AND owner_user_id = ?
                    """
                ),
                (document_id, project_id, owner_user_id),
            ).fetchone()
            if not row:
                raise ValueError("Document not found")
            connection.execute(
                self._sql("DELETE FROM documents WHERE id = ?"),
                (document_id,),
            )
        return str(row["storage_path"])

    def add_artifact(
        self,
        owner_user_id: str,
        *,
        artifact_type: str,
        filename: str,
        mime_type: str,
        storage_path: str,
        project_id: str | None = None,
        conversation_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        if self.artifacts_today(owner_user_id) >= MAX_ARTIFACTS_PER_USER_DAY:
            raise ValueError("Daily artifact limit reached")
        if project_id:
            self.get_project(owner_user_id, project_id)
        if conversation_id:
            self.get_conversation(owner_user_id, conversation_id)
        artifact_id = str(uuid.uuid4())
        with self._connect() as connection:
            connection.execute(
                self._sql(
                    """
                    INSERT INTO artifacts
                        (id, owner_user_id, project_id, conversation_id,
                         artifact_type, filename, mime_type, storage_path,
                         metadata_json, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                ),
                (
                    artifact_id,
                    owner_user_id,
                    project_id,
                    conversation_id,
                    artifact_type,
                    filename[:255],
                    mime_type,
                    storage_path,
                    json.dumps(metadata or {}, ensure_ascii=False),
                    utc_now(),
                ),
            )
        return artifact_id

    def get_artifact(self, owner_user_id: str, artifact_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                self._sql("SELECT * FROM artifacts WHERE id = ? AND owner_user_id = ?"),
                (artifact_id, owner_user_id),
            ).fetchone()
        if not row:
            raise ValueError("Artifact not found")
        item = dict(row)
        item["metadata"] = json.loads(item.pop("metadata_json") or "{}")
        return item

    def list_artifacts(
        self,
        owner_user_id: str,
        *,
        project_id: str | None = None,
        conversation_id: str | None = None,
    ) -> list[dict[str, Any]]:
        clauses = ["owner_user_id = ?"]
        parameters: list[Any] = [owner_user_id]
        if project_id:
            clauses.append("project_id = ?")
            parameters.append(project_id)
        if conversation_id:
            clauses.append("conversation_id = ?")
            parameters.append(conversation_id)
        with self._connect() as connection:
            rows = connection.execute(
                self._sql(
                    "SELECT * FROM artifacts WHERE "
                    + " AND ".join(clauses)
                    + " ORDER BY created_at DESC"
                ),
                parameters,
            ).fetchall()
        return [dict(row) for row in rows]

    def artifacts_today(self, owner_user_id: str) -> int:
        day_prefix = datetime.now(UTC).date().isoformat() + "%"
        with self._connect() as connection:
            row = connection.execute(
                self._sql(
                    """
                    SELECT COUNT(*) AS count FROM artifacts
                    WHERE owner_user_id = ? AND created_at LIKE ?
                    """
                ),
                (owner_user_id, day_prefix),
            ).fetchone()
        return int(row["count"])

    def check_rate_limit(self, user_id: str, mode: str = "standard") -> PilotRateLimit:
        now = datetime.now(UTC)
        day = now.date().isoformat()
        with self._connect() as connection:
            user_count = int(
                connection.execute(
                    self._sql(
                        """
                        SELECT COUNT(*) AS count FROM query_events
                        WHERE user_id = ? AND day_utc = ?
                        """
                    ),
                    (user_id, day),
                ).fetchone()["count"]
            )
            global_count = int(
                connection.execute(
                    self._sql(
                        "SELECT COUNT(*) AS count FROM query_events WHERE day_utc = ?"
                    ),
                    (day,),
                ).fetchone()["count"]
            )
            deep_count = int(
                connection.execute(
                    self._sql(
                        """
                        SELECT COUNT(*) AS count FROM query_events
                        WHERE user_id = ? AND day_utc = ? AND mode = 'deep'
                        """
                    ),
                    (user_id, day),
                ).fetchone()["count"]
            )
            last = connection.execute(
                self._sql(
                    """
                    SELECT occurred_at FROM query_events
                    WHERE user_id = ? ORDER BY occurred_at DESC LIMIT 1
                    """
                ),
                (user_id,),
            ).fetchone()

            remaining = max(0, MAX_QUERIES_PER_USER_DAY - user_count)
            if user_count >= MAX_QUERIES_PER_USER_DAY:
                return PilotRateLimit(False, "Daily user query limit reached.", 0)
            if global_count >= MAX_PILOT_QUERIES_PER_DAY:
                return PilotRateLimit(False, "Daily pilot limit reached.", remaining)
            if mode == "deep" and deep_count >= MAX_DEEP_QUERIES_PER_USER_DAY:
                return PilotRateLimit(
                    False, "Daily Deep-mode limit reached.", remaining
                )
            if last:
                elapsed = (
                    now - datetime.fromisoformat(str(last["occurred_at"]))
                ).total_seconds()
                if elapsed < PILOT_COOLDOWN_SECONDS:
                    return PilotRateLimit(
                        False,
                        "Please wait briefly before another query.",
                        remaining,
                    )

            connection.execute(
                self._sql(
                    """
                    INSERT INTO query_events
                        (occurred_at, day_utc, user_id, mode)
                    VALUES (?, ?, ?, ?)
                    """
                ),
                (now.isoformat(), day, user_id, mode),
            )
        return PilotRateLimit(True, None, max(0, remaining - 1))

    def complete_query(
        self,
        user_id: str,
        *,
        mode: str,
        language: str,
        duration_ms: int,
        success: bool,
        error_type: str | None = None,
        trusted_searches: int = 0,
    ) -> None:
        with self._connect() as connection:
            row = connection.execute(
                self._sql(
                    """
                    SELECT id FROM query_events
                    WHERE user_id = ? AND mode = ? AND duration_ms IS NULL
                    ORDER BY id DESC LIMIT 1
                    """
                ),
                (user_id, mode),
            ).fetchone()
            if row:
                connection.execute(
                    self._sql(
                        """
                        UPDATE query_events
                        SET language = ?, duration_ms = ?, success = ?,
                            error_type = ?, trusted_searches = ?
                        WHERE id = ?
                        """
                    ),
                    (
                        language,
                        int(duration_ms),
                        int(success),
                        error_type,
                        int(trusted_searches),
                        row["id"],
                    ),
                )

    def record_feedback(
        self,
        *,
        category: str,
        comment: str,
        consent: bool,
        user_id: str | None = None,
        message_id: str | None = None,
        rating: int | None = None,
        language: str | None = None,
        session_id: str | None = None,
    ) -> int:
        if not consent:
            raise ValueError("Consent is required before recording feedback")
        cleaned = " ".join((comment or "").split()).strip()
        if not cleaned or len(cleaned) > 2000:
            raise ValueError("Feedback must be 1–2000 characters")
        if rating is not None and rating not in {1, 2, 3, 4, 5}:
            raise ValueError("Rating must be between 1 and 5")
        allowed = {
            "knowledge_gap",
            "incorrect_answer",
            "local_language",
            "usability",
            "safety",
            "helpful",
            "not_helpful",
            "other",
        }
        if category not in allowed:
            raise ValueError("Unknown feedback category")
        del session_id
        with self._connect() as connection:
            cursor = connection.execute(
                self._sql(
                    """
                    INSERT INTO feedback
                        (occurred_at, user_id, message_id, category, rating,
                         comment, language, consent)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """
                ),
                (
                    utc_now(),
                    user_id,
                    message_id,
                    category,
                    rating,
                    cleaned,
                    language,
                    1,
                ),
            )
            if self.is_postgres:
                row = connection.execute("SELECT LASTVAL() AS id").fetchone()
                return int(row["id"])
            return int(cursor.lastrowid)

    def feedback_summary(self) -> dict[str, Any]:
        with self._connect() as connection:
            total = int(
                connection.execute("SELECT COUNT(*) AS count FROM feedback").fetchone()[
                    "count"
                ]
            )
            validated = int(
                connection.execute(
                    """
                    SELECT COUNT(*) AS count FROM feedback
                    WHERE priority = 'high' AND status != 'new'
                    """
                ).fetchone()["count"]
            )
            resolved = int(
                connection.execute(
                    """
                    SELECT COUNT(*) AS count FROM feedback
                    WHERE priority = 'high' AND status IN ('resolved', 'verified')
                    """
                ).fetchone()["count"]
            )
        return {
            "total_feedback": total,
            "validated_high_priority": validated,
            "resolved_high_priority": resolved,
            "resolution_percent": (
                round(resolved / validated * 100, 1) if validated else None
            ),
        }

    def performance_summary(self) -> dict[str, Any]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT duration_ms, success FROM query_events
                WHERE duration_ms IS NOT NULL ORDER BY duration_ms
                """
            ).fetchall()
        durations = [int(row["duration_ms"]) for row in rows]
        if not durations:
            return {
                "measured_queries": 0,
                "median_response_ms": None,
                "success_percent": None,
            }
        middle = len(durations) // 2
        median = (
            durations[middle]
            if len(durations) % 2
            else int((durations[middle - 1] + durations[middle]) / 2)
        )
        successes = sum(int(row["success"] or 0) for row in rows)
        return {
            "measured_queries": len(durations),
            "median_response_ms": median,
            "success_percent": round(successes / len(durations) * 100, 1),
        }

    def register_whatsapp_event(
        self,
        message_id: str,
        identity_hash: str,
    ) -> bool:
        try:
            with self._connect() as connection:
                connection.execute(
                    self._sql(
                        """
                        INSERT INTO whatsapp_events
                            (message_id, identity_hash, status, received_at)
                        VALUES (?, ?, 'queued', ?)
                        """
                    ),
                    (message_id, identity_hash, utc_now()),
                )
            return True
        except Exception as exc:  # uniqueness is the deduplication boundary
            if "unique" in str(exc).lower() or "duplicate" in str(exc).lower():
                return False
            raise

    def complete_whatsapp_event(
        self,
        message_id: str,
        *,
        status: str,
        error_type: str | None = None,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                self._sql(
                    """
                    UPDATE whatsapp_events
                    SET status = ?, error_type = ?, completed_at = ?
                    WHERE message_id = ?
                    """
                ),
                (status, error_type, utc_now(), message_id),
            )


def hash_external_identity(value: str, secret: str) -> str:
    if not secret:
        raise ValueError("Identity hashing secret is not configured")
    return hmac.new(
        secret.encode("utf-8"),
        value.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
