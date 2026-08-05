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
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from .auth import UserIdentity
from .config import (
    CONSENT_VERSION,
    DATABASE_POOL_MAX_SIZE,
    DATABASE_POOL_MIN_SIZE,
    DATABASE_URL,
    LOCAL_PILOT_DB_PATH,
    MAX_ARTIFACTS_PER_USER_DAY,
    MAX_DEEP_QUERIES_PER_USER_DAY,
    MAX_PILOT_QUERIES_PER_DAY,
    MAX_QUERIES_PER_USER_DAY,
    MAX_USER_WEEKLY_COST_USD,
    PILOT_COOLDOWN_SECONDS,
)


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _week_bounds(now: datetime) -> tuple[str, str]:
    """Return the [start, end) ISO timestamps of the Monday-start UTC week."""

    monday = now.date() - timedelta(days=now.weekday())
    start = datetime(monday.year, monday.month, monday.day, tzinfo=UTC)
    end = start + timedelta(days=7)
    return start.isoformat(), end.isoformat()


@dataclass(frozen=True)
class PilotRateLimit:
    allowed: bool
    message: str | None
    remaining_user: int


@dataclass(frozen=True)
class WeeklyUsage:
    spend_usd: float
    limit_usd: float
    week_start: str
    week_end: str


class PilotStore:
    """Application persistence that fails closed on ownership checks."""

    def __init__(
        self,
        database_url: str | None = None,
        sqlite_path: str | Path | None = None,
    ) -> None:
        # Passing a SQLite path is an explicit local-only choice. This prevents
        # tests and maintenance scripts from silently using a DATABASE_URL that
        # happens to be present in the developer's environment.
        if database_url is None:
            database_url = "" if sqlite_path is not None else DATABASE_URL
        self.database_url = database_url.strip()
        self.sqlite_path = Path(sqlite_path or LOCAL_PILOT_DB_PATH)
        self.is_postgres = self.database_url.startswith(
            ("postgres://", "postgresql://")
        )
        self._pool: Any | None = None
        if self.is_postgres:
            try:
                from psycopg.rows import dict_row
                from psycopg_pool import ConnectionPool
            except ImportError as exc:  # pragma: no cover - deployment dependency
                raise RuntimeError(
                    "PostgreSQL support requires psycopg and psycopg-pool"
                ) from exc
            self._pool = ConnectionPool(
                conninfo=self.database_url,
                min_size=max(1, DATABASE_POOL_MIN_SIZE),
                max_size=max(DATABASE_POOL_MIN_SIZE, DATABASE_POOL_MAX_SIZE),
                kwargs={"row_factory": dict_row},
                open=True,
            )
        if not self.is_postgres:
            self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @contextmanager
    def _connect(self) -> Iterator[Any]:
        if self.is_postgres:
            if self._pool is None:  # pragma: no cover - defensive guard
                raise RuntimeError("PostgreSQL pool is not initialized")
            with self._pool.connection() as connection:
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

    def close(self) -> None:
        if self._pool is not None:
            self._pool.close()

    def _initialize(self) -> None:
        if self.is_postgres:
            migrations = Path(__file__).resolve().parents[1] / "migrations"
            with self._connect() as connection:
                for migration in sorted(migrations.glob("*.sql")):
                    connection.execute(migration.read_text(encoding="utf-8"))
            return

        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    issuer TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    auth_user_id TEXT,
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
                CREATE UNIQUE INDEX IF NOT EXISTS idx_users_auth_user_id
                    ON users(auth_user_id);
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
                    trusted_searches INTEGER NOT NULL DEFAULT 0,
                    request_id TEXT,
                    ttft_ms INTEGER,
                    stage_durations_json TEXT NOT NULL DEFAULT '{}',
                    prompt_tokens INTEGER,
                    completion_tokens INTEGER,
                    estimated_cost_usd REAL
                );
                CREATE INDEX IF NOT EXISTS idx_pilot_query_day
                    ON query_events(day_utc);
                CREATE INDEX IF NOT EXISTS idx_pilot_query_user
                    ON query_events(user_id, occurred_at);
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
            self._ensure_sqlite_upgrades(connection)

    @staticmethod
    def _ensure_sqlite_upgrades(connection: sqlite3.Connection) -> None:
        columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(users)")
        }
        if "auth_user_id" not in columns:
            connection.execute("ALTER TABLE users ADD COLUMN auth_user_id TEXT")
            connection.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_auth_user_id "
                "ON users(auth_user_id)"
            )

        query_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(query_events)")
        }
        additions = {
            "request_id": "TEXT",
            "ttft_ms": "INTEGER",
            "stage_durations_json": "TEXT NOT NULL DEFAULT '{}'",
            "prompt_tokens": "INTEGER",
            "completion_tokens": "INTEGER",
            "estimated_cost_usd": "REAL",
        }
        for name, definition in additions.items():
            if name not in query_columns:
                connection.execute(
                    f"ALTER TABLE query_events ADD COLUMN {name} {definition}"
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

    def upsert_supabase_user(
        self,
        *,
        auth_user_id: str,
        email: str,
        name: str,
        google_subject: str | None,
        is_admin: bool,
    ) -> dict[str, Any]:
        """Link a verified Supabase identity without using email as a key."""

        auth_user_id = auth_user_id.strip()
        if not auth_user_id:
            raise ValueError("Supabase identity is missing its subject")
        now = utc_now()
        role = "admin" if is_admin else "user"
        with self._connect() as connection:
            row = connection.execute(
                self._sql("SELECT * FROM users WHERE auth_user_id = ?"),
                (auth_user_id,),
            ).fetchone()
            if not row and google_subject:
                row = connection.execute(
                    self._sql(
                        """
                        SELECT * FROM users
                        WHERE issuer IN ('accounts.google.com',
                                         'https://accounts.google.com')
                          AND subject = ?
                        """
                    ),
                    (google_subject,),
                ).fetchone()
            if row:
                connection.execute(
                    self._sql(
                        """
                        UPDATE users
                        SET auth_user_id = ?, email = ?, name = ?, role = ?,
                            last_seen_at = ?
                        WHERE id = ?
                        """
                    ),
                    (
                        auth_user_id,
                        email or None,
                        name[:200],
                        role,
                        now,
                        row["id"],
                    ),
                )
                user_id = str(row["id"])
            else:
                user_id = str(uuid.uuid4())
                issuer = "https://accounts.google.com" if google_subject else "supabase"
                subject = google_subject or auth_user_id
                connection.execute(
                    self._sql(
                        """
                        INSERT INTO users
                            (id, issuer, subject, auth_user_id, email, name, role,
                             created_at, last_seen_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """
                    ),
                    (
                        user_id,
                        issuer,
                        subject,
                        auth_user_id,
                        email or None,
                        name[:200],
                        role,
                        now,
                        now,
                    ),
                )
        return self.get_user(user_id)

    def get_user_by_auth_id(self, auth_user_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                self._sql("SELECT * FROM users WHERE auth_user_id = ?"),
                (auth_user_id,),
            ).fetchone()
        if not row:
            raise ValueError("User not found")
        return dict(row)

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

    def user_storage_paths(self, user_id: str) -> list[str]:
        """Return every private object path owned by a user."""

        self.get_user(user_id)
        paths: list[str] = []
        with self._connect() as connection:
            for table in ("documents", "artifacts", "uploads"):
                rows = connection.execute(
                    self._sql(
                        f"SELECT storage_path FROM {table} WHERE owner_user_id = ?"
                    ),
                    (user_id,),
                ).fetchall()
                paths.extend(str(row["storage_path"]) for row in rows)
            rows = connection.execute(
                self._sql(
                    """
                    SELECT m.attachments_json FROM messages m
                    JOIN conversations c ON c.id = m.conversation_id
                    WHERE c.owner_user_id = ?
                    """
                ),
                (user_id,),
            ).fetchall()
        for row in rows:
            for attachment in json.loads(row["attachments_json"] or "[]"):
                path = attachment.get("storage_path")
                if path:
                    paths.append(str(path))
        return list(dict.fromkeys(paths))

    def storage_inventory(self) -> list[dict[str, Any]]:
        """Return provider-neutral metadata for every referenced private object."""

        inventory: dict[str, dict[str, Any]] = {}
        with self._connect() as connection:
            documents = connection.execute(
                """
                SELECT storage_path, mime_type, sha256, size_bytes
                FROM documents ORDER BY storage_path
                """
            ).fetchall()
            artifacts = connection.execute(
                """
                SELECT storage_path, mime_type
                FROM artifacts ORDER BY storage_path
                """
            ).fetchall()
            messages = connection.execute(
                "SELECT attachments_json FROM messages ORDER BY created_at"
            ).fetchall()
        for row in documents:
            path = str(row["storage_path"])
            inventory[path] = {
                "storage_path": path,
                "kind": "document",
                "mime_type": str(row["mime_type"]),
                "expected_sha256": str(row["sha256"]),
                "expected_size_bytes": int(row["size_bytes"]),
            }
        for row in artifacts:
            path = str(row["storage_path"])
            inventory.setdefault(
                path,
                {
                    "storage_path": path,
                    "kind": "artifact",
                    "mime_type": str(row["mime_type"]),
                    "expected_sha256": None,
                    "expected_size_bytes": None,
                },
            )
        for row in messages:
            for attachment in json.loads(row["attachments_json"] or "[]"):
                path = attachment.get("storage_path")
                if not path:
                    continue
                path = str(path)
                inventory.setdefault(
                    path,
                    {
                        "storage_path": path,
                        "kind": str(attachment.get("kind") or "attachment"),
                        "mime_type": str(
                            attachment.get("mime_type") or "application/octet-stream"
                        ),
                        "expected_sha256": attachment.get("sha256"),
                        "expected_size_bytes": attachment.get("size_bytes"),
                    },
                )
        return [inventory[path] for path in sorted(inventory)]

    def delete_user_records(self, user_id: str) -> None:
        """Delete identity/content and retain only anonymous aggregate events."""

        user = self.get_user(user_id)
        with self._connect() as connection:
            connection.execute(
                self._sql("DELETE FROM feedback WHERE user_id = ?"),
                (user_id,),
            )
            connection.execute(
                self._sql("UPDATE query_events SET user_id = NULL WHERE user_id = ?"),
                (user_id,),
            )
            if user.get("issuer") == "whatsapp-cloud-api":
                connection.execute(
                    self._sql("DELETE FROM whatsapp_events WHERE identity_hash = ?"),
                    (user.get("subject"),),
                )
            cursor = connection.execute(
                self._sql("DELETE FROM users WHERE id = ?"),
                (user_id,),
            )
            if cursor.rowcount != 1:
                raise ValueError("User not found")

    def export_user_data(self, user_id: str) -> dict[str, Any]:
        """Return a portable copy of a user's active workspace data."""

        user = self.get_user(user_id)
        with self._connect() as connection:
            projects = [
                dict(row)
                for row in connection.execute(
                    self._sql("SELECT * FROM projects WHERE owner_user_id = ?"),
                    (user_id,),
                ).fetchall()
            ]
            conversations = [
                dict(row)
                for row in connection.execute(
                    self._sql("SELECT * FROM conversations WHERE owner_user_id = ?"),
                    (user_id,),
                ).fetchall()
            ]
            messages = [
                dict(row)
                for row in connection.execute(
                    self._sql(
                        """
                        SELECT m.* FROM messages m
                        JOIN conversations c ON c.id = m.conversation_id
                        WHERE c.owner_user_id = ? ORDER BY m.created_at
                        """
                    ),
                    (user_id,),
                ).fetchall()
            ]
            documents = [
                dict(row)
                for row in connection.execute(
                    self._sql("SELECT * FROM documents WHERE owner_user_id = ?"),
                    (user_id,),
                ).fetchall()
            ]
            artifacts = [
                dict(row)
                for row in connection.execute(
                    self._sql("SELECT * FROM artifacts WHERE owner_user_id = ?"),
                    (user_id,),
                ).fetchall()
            ]
            feedback = [
                dict(row)
                for row in connection.execute(
                    self._sql("SELECT * FROM feedback WHERE user_id = ?"),
                    (user_id,),
                ).fetchall()
            ]
            query_events = [
                dict(row)
                for row in connection.execute(
                    self._sql("SELECT * FROM query_events WHERE user_id = ?"),
                    (user_id,),
                ).fetchall()
            ]
        for message in messages:
            for field in (
                "citations_json",
                "tools_json",
                "artifacts_json",
                "attachments_json",
            ):
                message[field.removesuffix("_json")] = json.loads(
                    message.pop(field) or "[]"
                )
        for artifact in artifacts:
            artifact["metadata"] = json.loads(artifact.pop("metadata_json") or "{}")
        return {
            "exported_at": utc_now(),
            "user": user,
            "projects": projects,
            "conversations": conversations,
            "messages": messages,
            "documents": documents,
            "artifacts": artifacts,
            "feedback": feedback,
            "query_events": query_events,
            "note": (
                "Original uploaded files and generated artifact binaries are not "
                "embedded in this JSON export. Download them from their cards."
            ),
        }

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

    def project_storage_paths(self, owner_user_id: str, project_id: str) -> list[str]:
        """Return private objects that will be removed with a project."""

        documents = self.list_documents(owner_user_id, project_id)
        artifacts = self.list_artifacts(owner_user_id, project_id=project_id)
        paths = [item["storage_path"] for item in [*documents, *artifacts]]
        return list(dict.fromkeys(paths))

    def delete_project(self, owner_user_id: str, project_id: str) -> list[str]:
        paths = self.project_storage_paths(owner_user_id, project_id)
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

    def set_conversation_archived(
        self,
        owner_user_id: str,
        conversation_id: str,
        archived: bool,
    ) -> None:
        with self._connect() as connection:
            cursor = connection.execute(
                self._sql(
                    """
                    UPDATE conversations
                    SET archived = ?, updated_at = ?
                    WHERE id = ? AND owner_user_id = ?
                    """
                ),
                (int(bool(archived)), utc_now(), conversation_id, owner_user_id),
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
        paths = self.conversation_storage_paths(owner_user_id, conversation_id)
        with self._connect() as connection:
            cursor = connection.execute(
                self._sql(
                    "DELETE FROM conversations WHERE id = ? AND owner_user_id = ?"
                ),
                (conversation_id, owner_user_id),
            )
            if cursor.rowcount != 1:
                raise ValueError("Conversation not found")
        return paths

    def conversation_storage_paths(
        self, owner_user_id: str, conversation_id: str
    ) -> list[str]:
        """Return private objects that will be removed with a conversation."""

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

    def owns_message(self, owner_user_id: str, message_id: str) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                self._sql(
                    """
                    SELECT 1
                    FROM messages m
                    JOIN conversations c ON c.id = m.conversation_id
                    WHERE m.id = ? AND c.owner_user_id = ?
                    """
                ),
                (message_id, owner_user_id),
            ).fetchone()
        return bool(row)

    def list_messages(
        self,
        owner_user_id: str,
        conversation_id: str,
        *,
        limit: int = 200,
        before: str | None = None,
    ) -> list[dict[str, Any]]:
        self.get_conversation(owner_user_id, conversation_id)
        clauses = ["conversation_id = ?"]
        parameters: list[Any] = [conversation_id]
        if before:
            clauses.append("created_at < ?")
            parameters.append(before)
        parameters.append(max(1, min(int(limit), 500)))
        with self._connect() as connection:
            rows = connection.execute(
                self._sql(
                    "SELECT * FROM messages WHERE "
                    + " AND ".join(clauses)
                    + " ORDER BY created_at DESC LIMIT ?"
                ),
                parameters,
            ).fetchall()
        messages = []
        for row in reversed(rows):
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

    def create_upload(
        self,
        owner_user_id: str,
        *,
        storage_path: str,
        mime_type: str,
        size_bytes: int,
        expires_at: str,
    ) -> str:
        self.get_user(owner_user_id)
        upload_id = str(uuid.uuid4())
        with self._connect() as connection:
            connection.execute(
                self._sql(
                    """
                    INSERT INTO uploads
                        (id, owner_user_id, storage_path, mime_type, size_bytes,
                         status, created_at, expires_at)
                    VALUES (?, ?, ?, ?, ?, 'ready', ?, ?)
                    """
                ),
                (
                    upload_id,
                    owner_user_id,
                    storage_path,
                    mime_type,
                    int(size_bytes),
                    utc_now(),
                    expires_at,
                ),
            )
        return upload_id

    def get_upload(self, owner_user_id: str, upload_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                self._sql(
                    """
                    SELECT * FROM uploads
                    WHERE id = ? AND owner_user_id = ? AND status = 'ready'
                    """
                ),
                (upload_id, owner_user_id),
            ).fetchone()
        if not row:
            raise ValueError("Upload not found")
        item = dict(row)
        if datetime.fromisoformat(str(item["expires_at"])) <= datetime.now(UTC):
            raise ValueError("Upload expired")
        return item

    def consume_upload(self, owner_user_id: str, upload_id: str) -> None:
        with self._connect() as connection:
            cursor = connection.execute(
                self._sql(
                    """
                    UPDATE uploads SET status = 'consumed'
                    WHERE id = ? AND owner_user_id = ? AND status = 'ready'
                    """
                ),
                (upload_id, owner_user_id),
            )
            if cursor.rowcount != 1:
                raise ValueError("Upload not found")

    def create_assistant_turn(
        self,
        owner_user_id: str,
        conversation_id: str,
        *,
        user_message_id: str,
        clarification_count: int,
    ) -> str:
        self.get_conversation(owner_user_id, conversation_id)
        turn_id = str(uuid.uuid4())
        now = utc_now()
        with self._connect() as connection:
            connection.execute(
                self._sql(
                    """
                    INSERT INTO assistant_turns
                        (id, owner_user_id, conversation_id, user_message_id,
                         status, clarification_count, created_at, updated_at)
                    VALUES (?, ?, ?, ?, 'analyzing', ?, ?, ?)
                    """
                ),
                (
                    turn_id,
                    owner_user_id,
                    conversation_id,
                    user_message_id,
                    max(0, int(clarification_count)),
                    now,
                    now,
                ),
            )
        return turn_id

    def complete_assistant_turn(
        self,
        owner_user_id: str,
        turn_id: str,
        *,
        status: str,
        analysis: dict[str, Any],
        assistant_message_id: str | None = None,
        error_type: str | None = None,
    ) -> None:
        with self._connect() as connection:
            cursor = connection.execute(
                self._sql(
                    """
                    UPDATE assistant_turns
                    SET status = ?, analysis_json = ?, assistant_message_id = ?,
                        error_type = ?, updated_at = ?
                    WHERE id = ? AND owner_user_id = ?
                    """
                ),
                (
                    status,
                    json.dumps(analysis, ensure_ascii=False),
                    assistant_message_id,
                    error_type,
                    utc_now(),
                    turn_id,
                    owner_user_id,
                ),
            )
            if cursor.rowcount != 1:
                raise ValueError("Assistant turn not found")

    def consecutive_clarifications(
        self,
        owner_user_id: str,
        conversation_id: str,
    ) -> int:
        messages = self.list_messages(owner_user_id, conversation_id, limit=8)
        count = 0
        for message in reversed(messages):
            if message["role"] == "assistant" and message["status"] == "clarification":
                count += 1
                continue
            if message["role"] == "user" and count:
                continue
            if message["role"] == "assistant":
                break
        return count

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
        week_start, week_end = _week_bounds(now)
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
            weekly_spend = float(
                connection.execute(
                    self._sql(
                        """
                        SELECT COALESCE(SUM(estimated_cost_usd), 0) AS spend
                        FROM query_events
                        WHERE user_id = ? AND occurred_at >= ? AND occurred_at < ?
                        """
                    ),
                    (user_id, week_start, week_end),
                ).fetchone()["spend"]
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
            if weekly_spend >= MAX_USER_WEEKLY_COST_USD:
                return PilotRateLimit(
                    False, "Weekly spending limit reached.", remaining
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

    def get_weekly_usage(self, user_id: str) -> WeeklyUsage:
        now = datetime.now(UTC)
        week_start, week_end = _week_bounds(now)
        with self._connect() as connection:
            spend = float(
                connection.execute(
                    self._sql(
                        """
                        SELECT COALESCE(SUM(estimated_cost_usd), 0) AS spend
                        FROM query_events
                        WHERE user_id = ? AND occurred_at >= ? AND occurred_at < ?
                        """
                    ),
                    (user_id, week_start, week_end),
                ).fetchone()["spend"]
            )
        return WeeklyUsage(
            spend_usd=round(spend, 4),
            limit_usd=MAX_USER_WEEKLY_COST_USD,
            week_start=week_start,
            week_end=week_end,
        )

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
        request_id: str | None = None,
        ttft_ms: int | None = None,
        stage_durations: dict[str, int] | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        estimated_cost_usd: float | None = None,
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
                            error_type = ?, trusted_searches = ?,
                            request_id = ?, ttft_ms = ?,
                            stage_durations_json = ?, prompt_tokens = ?,
                            completion_tokens = ?, estimated_cost_usd = ?
                        WHERE id = ?
                        """
                    ),
                    (
                        language,
                        int(duration_ms),
                        int(success),
                        error_type,
                        int(trusted_searches),
                        request_id,
                        int(ttft_ms) if ttft_ms is not None else None,
                        json.dumps(stage_durations or {}, sort_keys=True),
                        int(prompt_tokens) if prompt_tokens is not None else None,
                        (
                            int(completion_tokens)
                            if completion_tokens is not None
                            else None
                        ),
                        (
                            float(estimated_cost_usd)
                            if estimated_cost_usd is not None
                            else None
                        ),
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
