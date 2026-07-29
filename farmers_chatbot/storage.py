"""Small local evidence store for rate limits, telemetry, and feedback."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .config import (
    COOLDOWN_SECONDS,
    MAX_QUERIES_PER_DAY_GLOBAL,
    MAX_QUERIES_PER_SESSION,
)


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    message: str | None
    remaining_session: int


class EvidenceStore:
    """SQLite-backed local store.

    SQLite provides atomicity for a single deployed instance. A multi-replica pilot
    must use a shared external store and provider-enforced spending controls.
    """

    def __init__(self, path: str | Path = "data/runtime.sqlite3") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS query_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    occurred_at TEXT NOT NULL,
                    day_utc TEXT NOT NULL,
                    session_hash TEXT NOT NULL,
                    mode TEXT,
                    language TEXT,
                    duration_ms INTEGER,
                    success INTEGER,
                    error_type TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_query_day
                    ON query_events(day_utc);
                CREATE INDEX IF NOT EXISTS idx_query_session
                    ON query_events(session_hash, occurred_at);

                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    occurred_at TEXT NOT NULL,
                    session_hash TEXT NOT NULL,
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
                """
            )

    @staticmethod
    def session_hash(session_id: str) -> str:
        return hashlib.sha256(session_id.encode("utf-8")).hexdigest()[:24]

    def check_rate_limit(self, session_id: str) -> RateLimitResult:
        now = datetime.now(UTC)
        now_text = now.isoformat()
        day = now.date().isoformat()
        session_hash = self.session_hash(session_id)

        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            session_count = int(
                connection.execute(
                    "SELECT COUNT(*) FROM query_events WHERE session_hash = ?",
                    (session_hash,),
                ).fetchone()[0]
            )
            global_count = int(
                connection.execute(
                    "SELECT COUNT(*) FROM query_events WHERE day_utc = ?",
                    (day,),
                ).fetchone()[0]
            )
            last_row = connection.execute(
                """
                SELECT occurred_at
                FROM query_events
                WHERE session_hash = ?
                ORDER BY occurred_at DESC
                LIMIT 1
                """,
                (session_hash,),
            ).fetchone()

            remaining = max(0, MAX_QUERIES_PER_SESSION - session_count)
            if session_count >= MAX_QUERIES_PER_SESSION:
                return RateLimitResult(
                    False,
                    f"Session limit reached ({MAX_QUERIES_PER_SESSION}).",
                    0,
                )
            if global_count >= MAX_QUERIES_PER_DAY_GLOBAL:
                return RateLimitResult(False, "Daily pilot limit reached.", remaining)
            if last_row:
                last = datetime.fromisoformat(last_row["occurred_at"])
                elapsed = (now - last).total_seconds()
                if elapsed < COOLDOWN_SECONDS:
                    wait = max(1, int(COOLDOWN_SECONDS - elapsed) + 1)
                    return RateLimitResult(
                        False,
                        f"Please wait {wait} seconds before another query.",
                        remaining,
                    )

            connection.execute(
                """
                INSERT INTO query_events
                    (occurred_at, day_utc, session_hash)
                VALUES (?, ?, ?)
                """,
                (now_text, day, session_hash),
            )
            return RateLimitResult(True, None, max(0, remaining - 1))

    def complete_query(
        self,
        session_id: str,
        *,
        mode: str,
        language: str,
        duration_ms: int,
        success: bool,
        error_type: str | None = None,
    ) -> None:
        session_hash = self.session_hash(session_id)
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id FROM query_events
                WHERE session_hash = ? AND mode IS NULL
                ORDER BY id DESC
                LIMIT 1
                """,
                (session_hash,),
            ).fetchone()
            if row:
                connection.execute(
                    """
                    UPDATE query_events
                    SET mode = ?, language = ?, duration_ms = ?, success = ?,
                        error_type = ?
                    WHERE id = ?
                    """,
                    (
                        mode,
                        language,
                        int(duration_ms),
                        int(success),
                        error_type,
                        row["id"],
                    ),
                )

    def record_feedback(
        self,
        *,
        session_id: str,
        category: str,
        comment: str,
        consent: bool,
        rating: int | None = None,
        language: str | None = None,
    ) -> int:
        if not consent:
            raise ValueError("Consent is required before recording feedback")
        cleaned = " ".join((comment or "").split()).strip()
        if not cleaned:
            raise ValueError("Feedback comment cannot be empty")
        if len(cleaned) > 2000:
            raise ValueError("Feedback comment must be 2000 characters or fewer")
        if rating is not None and rating not in {1, 2, 3, 4, 5}:
            raise ValueError("Rating must be between 1 and 5")
        allowed_categories = {
            "knowledge_gap",
            "incorrect_answer",
            "local_language",
            "usability",
            "safety",
            "other",
        }
        if category not in allowed_categories:
            raise ValueError("Unknown feedback category")

        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO feedback
                    (occurred_at, session_hash, category, rating, comment,
                     language, consent)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now(UTC).isoformat(),
                    self.session_hash(session_id),
                    category,
                    rating,
                    cleaned,
                    language,
                    1,
                ),
            )
            return int(cursor.lastrowid)

    def feedback_summary(self) -> dict[str, Any]:
        with self._connect() as connection:
            total = int(
                connection.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
            )
            validated_high = int(
                connection.execute(
                    """
                    SELECT COUNT(*) FROM feedback
                    WHERE priority = 'high' AND status != 'new'
                    """
                ).fetchone()[0]
            )
            resolved_high = int(
                connection.execute(
                    """
                    SELECT COUNT(*) FROM feedback
                    WHERE priority = 'high' AND status IN ('resolved', 'verified')
                    """
                ).fetchone()[0]
            )
        resolution_percent = (
            round(resolved_high / validated_high * 100, 1) if validated_high else None
        )
        return {
            "total_feedback": total,
            "validated_high_priority": validated_high,
            "resolved_high_priority": resolved_high,
            "resolution_percent": resolution_percent,
        }

    def list_feedback(self, status: str | None = None) -> list[dict[str, Any]]:
        query = (
            "SELECT id, occurred_at, category, rating, comment, language, "
            "status, priority, release_version, verification_note FROM feedback"
        )
        parameters: tuple[Any, ...] = ()
        if status:
            query += " WHERE status = ?"
            parameters = (status,)
        query += " ORDER BY id"
        with self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [dict(row) for row in rows]

    def update_feedback(
        self,
        feedback_id: int,
        *,
        status: str,
        priority: str | None = None,
        release_version: str | None = None,
        verification_note: str | None = None,
    ) -> None:
        allowed_statuses = {
            "new",
            "validated",
            "planned",
            "resolved",
            "verified",
            "rejected",
        }
        if status not in allowed_statuses:
            raise ValueError("Unknown feedback status")
        if priority not in {None, "low", "medium", "high"}:
            raise ValueError("Priority must be low, medium, or high")
        note = " ".join((verification_note or "").split()).strip() or None
        if note and len(note) > 2000:
            raise ValueError("Verification note must be 2000 characters or fewer")
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE feedback
                SET status = ?, priority = ?, release_version = ?,
                    verification_note = ?
                WHERE id = ?
                """,
                (status, priority, release_version, note, int(feedback_id)),
            )
            if cursor.rowcount != 1:
                raise ValueError("Feedback record not found")

    def performance_summary(self) -> dict[str, Any]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT duration_ms, success
                FROM query_events
                WHERE duration_ms IS NOT NULL
                ORDER BY duration_ms
                """
            ).fetchall()
        durations = [int(row["duration_ms"]) for row in rows]
        successes = sum(int(row["success"] or 0) for row in rows)
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
        return {
            "measured_queries": len(durations),
            "median_response_ms": median,
            "success_percent": round(successes / len(durations) * 100, 1),
        }


def load_logframe_status(
    path: str | Path = "data/logframe_status.json",
) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)
