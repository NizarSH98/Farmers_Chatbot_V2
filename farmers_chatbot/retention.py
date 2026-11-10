"""Pilot retention enforcement with a short identity window and a research window.

Two horizons apply, both measured back from now:

* ``retention_days`` (identity and files, at most 30 when hosted): uploaded
  documents, generated artifacts, and image attachments are deleted from private
  storage; attachment references inside kept messages are scrubbed; WhatsApp
  delivery records are deleted; and accounts inactive for longer lose their
  email and name. The account row, its pseudonymous participant code, and its
  conversation history stay, so research records remain linkable through the
  controlled stakeholder tracker without the database holding contact details.

* ``research_retention_days`` (interaction record): conversations, messages,
  turn analysis, and model-call records are deleted; query events and feedback
  lose their user link and survive only as anonymous aggregates; inactive
  accounts are deleted.

A person deleting their own account is separate and immediate; see
``PilotStore.delete_user_records``.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any

from .pilot_store import PilotStore


def purge_expired_content(
    store: PilotStore,
    retention_days: int,
    storage: Any | None = None,
    *,
    research_retention_days: int | None = None,
) -> list[str]:
    """Apply both retention horizons and return the private paths removed.

    When ``research_retention_days`` is omitted it equals ``retention_days``,
    which deletes the interaction record on the short horizon as well.
    """

    if retention_days < 1:
        raise ValueError("Retention must be at least one day")
    research_days = (
        retention_days if research_retention_days is None else research_retention_days
    )
    if research_days < retention_days:
        raise ValueError("Research retention cannot be shorter than file retention")
    now = datetime.now(UTC)
    file_cutoff = (now - timedelta(days=retention_days)).isoformat()
    research_cutoff = (now - timedelta(days=research_days)).isoformat()

    paths: list[str] = []
    scrubbed_messages: list[tuple[str, str]] = []
    with store._connect() as connection:
        message_rows = connection.execute(
            store._sql(
                """
                SELECT id, attachments_json FROM messages
                WHERE created_at < ?
                  AND position('storage_path' in attachments_json) > 0
                """
            ),
            (file_cutoff,),
        ).fetchall()
        for row in message_rows:
            attachments = json.loads(row["attachments_json"] or "[]")
            for attachment in attachments:
                storage_path = attachment.pop("storage_path", None)
                if storage_path:
                    paths.append(str(storage_path))
                    attachment["expired"] = True
            scrubbed_messages.append(
                (json.dumps(attachments, ensure_ascii=False), str(row["id"]))
            )

        document_rows = connection.execute(
            store._sql("SELECT storage_path FROM documents WHERE created_at < ?"),
            (file_cutoff,),
        ).fetchall()
        artifact_rows = connection.execute(
            store._sql(
                """
                SELECT storage_path FROM artifacts
                WHERE created_at < ? OR conversation_id IN (
                    SELECT id FROM conversations WHERE updated_at < ?
                )
                """
            ),
            (file_cutoff, research_cutoff),
        ).fetchall()
        paths.extend(str(row["storage_path"]) for row in document_rows)
        paths.extend(str(row["storage_path"]) for row in artifact_rows)

        # Private objects go first. If the provider fails, the exception leaves
        # every database reference in place so the next run can retry.
        if storage:
            for path in dict.fromkeys(paths):
                storage.delete(path)

        # Identity and file horizon.
        for attachments_json, message_id in scrubbed_messages:
            connection.execute(
                store._sql("UPDATE messages SET attachments_json = ? WHERE id = ?"),
                (attachments_json, message_id),
            )
        for statement in (
            "DELETE FROM artifacts WHERE created_at < ?",
            "DELETE FROM documents WHERE created_at < ?",
            "DELETE FROM whatsapp_events WHERE received_at < ?",
        ):
            connection.execute(store._sql(statement), (file_cutoff,))
        connection.execute(
            store._sql(
                """
                UPDATE users SET email = NULL, name = participant_code
                WHERE last_seen_at < ?
                  AND (email IS NOT NULL OR name <> participant_code)
                """
            ),
            (file_cutoff,),
        )

        # Research horizon.
        for statement in (
            "DELETE FROM messages WHERE created_at < ?",
            "DELETE FROM conversations WHERE updated_at < ?",
        ):
            connection.execute(store._sql(statement), (research_cutoff,))
        connection.execute(
            store._sql("UPDATE query_events SET user_id = NULL WHERE occurred_at < ?"),
            (research_cutoff,),
        )
        connection.execute(
            store._sql(
                """
                UPDATE feedback SET user_id = NULL, message_id = NULL
                WHERE occurred_at < ?
                """
            ),
            (research_cutoff,),
        )
        connection.execute(
            store._sql("DELETE FROM users WHERE last_seen_at < ?"),
            (research_cutoff,),
        )
    return list(dict.fromkeys(paths))
