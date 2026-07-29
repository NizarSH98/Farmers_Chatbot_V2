"""Pilot retention enforcement while preserving anonymous aggregate metrics."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from .pilot_store import PilotStore


def purge_expired_content(
    store: PilotStore,
    retention_days: int,
    storage: Any | None = None,
) -> list[str]:
    """Delete expired content and return private-storage paths to remove."""

    if retention_days < 1:
        raise ValueError("Retention must be at least one day")
    cutoff = (datetime.now(timezone.utc) - timedelta(days=retention_days)).isoformat()
    paths: list[str] = []
    with store._connect() as connection:  # noqa: SLF001 - store transaction boundary
        message_rows = connection.execute(
            store._sql(  # noqa: SLF001
                "SELECT attachments_json FROM messages WHERE created_at < ?"
            ),
            (cutoff,),
        ).fetchall()
        for row in message_rows:
            for attachment in json.loads(row["attachments_json"] or "[]"):
                storage_path = attachment.get("storage_path")
                if storage_path:
                    paths.append(str(storage_path))

        document_rows = connection.execute(
            store._sql(  # noqa: SLF001
                "SELECT storage_path FROM documents WHERE created_at < ?"
            ),
            (cutoff,),
        ).fetchall()
        artifact_rows = connection.execute(
            store._sql(  # noqa: SLF001
                """
                SELECT storage_path FROM artifacts
                WHERE created_at < ? OR conversation_id IN (
                    SELECT id FROM conversations WHERE updated_at < ?
                )
                """
            ),
            (cutoff, cutoff),
        ).fetchall()
        paths.extend(str(row["storage_path"]) for row in document_rows)
        paths.extend(str(row["storage_path"]) for row in artifact_rows)

        if storage:
            for path in dict.fromkeys(paths):
                storage.delete(path)

        for statement in (
            "DELETE FROM messages WHERE created_at < ?",
            "DELETE FROM artifacts WHERE created_at < ?",
            "DELETE FROM documents WHERE created_at < ?",
            "DELETE FROM conversations WHERE updated_at < ?",
            "DELETE FROM whatsapp_events WHERE received_at < ?",
        ):
            connection.execute(store._sql(statement), (cutoff,))  # noqa: SLF001
        connection.execute(
            store._sql(  # noqa: SLF001
                "UPDATE query_events SET user_id = NULL WHERE occurred_at < ?"
            ),
            (cutoff,),
        )
        connection.execute(
            store._sql(  # noqa: SLF001
                """
                UPDATE feedback SET user_id = NULL, message_id = NULL
                WHERE occurred_at < ?
                """
            ),
            (cutoff,),
        )
    return list(dict.fromkeys(paths))
