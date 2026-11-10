"""Build the pseudonymous pilot interaction dataset (roadmap deliverable D3).

Rows are keyed by participant code, never by email, name, or identity-provider
subject. The field team holds the code-to-person mapping in the controlled
stakeholder tracker, outside this database and outside this repository.

Free text (questions, answers, feedback comments) is exported as written. A
participant may still have typed something identifying, so the free-text
columns must be reviewed before the dataset leaves the project team.
"""

from __future__ import annotations

import json
from typing import Any

from .pilot_store import PilotStore

SCHEMA_VERSION = "raise.research-dataset.v1"

ANALYSIS_FIELDS = ("intent", "decision", "domain", "risk", "currentness", "location")


def _json(value: Any, default: Any) -> Any:
    if value in (None, ""):
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


def _participants(connection: Any) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT participant_code, role, issuer, consent_version, consent_at,
               created_at, last_seen_at, email IS NOT NULL AS contact_on_file
        FROM users ORDER BY created_at
        """
    ).fetchall()
    return [
        {
            "participant_code": row["participant_code"],
            "role": row["role"],
            "channel": (
                "whatsapp" if row["issuer"] == "whatsapp-cloud-api" else "web"
            ),
            "consent_version": row["consent_version"],
            "consent_at": row["consent_at"],
            "created_at": row["created_at"],
            "last_seen_at": row["last_seen_at"],
            "contact_on_file": bool(row["contact_on_file"]),
        }
        for row in rows
    ]


def _interactions(connection: Any) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT t.id AS turn_id, t.conversation_id, t.created_at, t.channel,
               t.status, t.clarification_count, t.analysis_json, t.error_type,
               u.participant_code,
               um.content AS question, um.language AS question_language,
               am.content AS answer, am.model, am.mode,
               am.citations_json, am.warning
        FROM assistant_turns t
        JOIN users u ON u.id = t.owner_user_id
        LEFT JOIN messages um ON um.id = t.user_message_id
        LEFT JOIN messages am ON am.id = t.assistant_message_id
        ORDER BY t.created_at
        """
    ).fetchall()
    interactions: list[dict[str, Any]] = []
    for row in rows:
        analysis = _json(row["analysis_json"], {})
        if not isinstance(analysis, dict):
            analysis = {}
        citations = _json(row["citations_json"], [])
        record = {
            "turn_id": row["turn_id"],
            "participant_code": row["participant_code"],
            "conversation_id": row["conversation_id"],
            "created_at": row["created_at"],
            "channel": row["channel"],
            "status": row["status"],
            "language": row["question_language"],
            "mode": row["mode"],
            "model": row["model"],
            "question": row["question"],
            "answer": row["answer"],
            "citation_count": len(citations) if isinstance(citations, list) else 0,
            "clarification_count": row["clarification_count"],
            "warning": row["warning"],
            "error_type": row["error_type"],
        }
        for field in ANALYSIS_FIELDS:
            record[field] = analysis.get(field)
        interactions.append(record)
    return interactions


def _query_events(connection: Any) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT u.participant_code, q.turn_id, q.occurred_at, q.day_utc, q.mode,
               q.language, q.query_status, q.success, q.error_type,
               q.duration_ms, q.ttft_ms, q.prompt_tokens, q.completion_tokens,
               q.estimated_cost_usd, q.trusted_searches
        FROM query_events q
        LEFT JOIN users u ON u.id = q.user_id
        ORDER BY q.occurred_at
        """
    ).fetchall()
    events = []
    for row in rows:
        event = dict(row)
        if event["estimated_cost_usd"] is not None:
            event["estimated_cost_usd"] = float(event["estimated_cost_usd"])
        events.append(event)
    return events


def _feedback(connection: Any) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT f.id AS feedback_id, u.participant_code, f.message_id,
               f.occurred_at, f.category, f.rating, f.comment, f.language,
               f.status, f.priority, f.release_version
        FROM feedback f
        LEFT JOIN users u ON u.id = f.user_id
        ORDER BY f.occurred_at
        """
    ).fetchall()
    return [dict(row) for row in rows]


def build_research_dataset(store: PilotStore) -> dict[str, list[dict[str, Any]]]:
    """Return the dataset as named tables of plain JSON-serialisable rows."""

    with store._connect() as connection:
        return {
            "participants": _participants(connection),
            "interactions": _interactions(connection),
            "query_events": _query_events(connection),
            "feedback": _feedback(connection),
        }
