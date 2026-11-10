"""Two-window retention, participant codes, and the research dataset.

These run against the test PostgreSQL database because their whole job is what
the SQL does to stored rows.
"""

import json
import re
from datetime import UTC, datetime, timedelta

import pytest
from conftest import new_pilot_store

from farmers_chatbot.auth import UserIdentity
from farmers_chatbot.research_export import build_research_dataset
from farmers_chatbot.retention import purge_expired_content

CODE_PATTERN = re.compile(r"^RAISE-[23456789ABCDEFGHJKMNPQRSTUVWXYZ]{6}$")


class _RecordingStorage:
    def __init__(self):
        self.deleted: list[str] = []

    def delete(self, path):
        self.deleted.append(path)


def _identity(subject="subject", email="farmer@example.org", name="Farmer"):
    return UserIdentity(
        user_id="",
        issuer="test",
        subject=subject,
        email=email,
        name=name,
        is_admin=False,
    )


def _days_ago(days: int) -> str:
    return (datetime.now(UTC) - timedelta(days=days)).isoformat()


def _completed_turn(store, user_id, *, question="When should I prune olives?"):
    conversation_id = store.create_conversation(user_id)
    reservation = store.reserve_assistant_turn(
        user_id,
        conversation_id,
        request_id="request-1",
        payload_sha256="hash",
        channel="web",
        mode="standard",
        language="english",
        user_content=question,
        attachments=[
            {"kind": "image", "storage_path": "users/u/old.jpg", "mime_type": "image/jpeg"}
        ],
        clarification_count=0,
        reserved_cost_usd=0.0,
    )
    assert reservation.allowed and reservation.turn_id
    assistant_message_id = store.finalize_assistant_turn(
        user_id,
        reservation.turn_id,
        turn_status="completed",
        message_content="Prune after harvest, before spring growth.",
        message_language="english",
        message_mode="standard",
        message_model="moonshotai/kimi-k3",
        message_status="complete",
        citations=[{"id": "source-1"}],
        tools=[],
        artifact_ids=[],
        warning=None,
        analysis={"intent": "how_to", "domain": "olive", "risk": "low"},
        duration_ms=4200,
        success=True,
        error_type=None,
        trusted_searches=0,
        ttft_ms=900,
        stage_durations={},
        prompt_tokens=100,
        completion_tokens=50,
        estimated_cost_usd=0.002,
        provider_calls=[],
        terminal_sequence=1,
    )
    return conversation_id, reservation, assistant_message_id


def _age_everything(store, days: int) -> None:
    stamp = _days_ago(days)
    with store._connect() as connection:
        connection.execute("UPDATE messages SET created_at = %s", (stamp,))
        connection.execute("UPDATE conversations SET updated_at = %s", (stamp,))
        connection.execute("UPDATE users SET last_seen_at = %s", (stamp,))
        connection.execute(
            "UPDATE query_events SET occurred_at = %s, day_utc = %s",
            (stamp, stamp[:10]),
        )
        connection.execute("UPDATE feedback SET occurred_at = %s", (stamp,))


def test_new_accounts_get_distinct_readable_participant_codes():
    store = new_pilot_store()
    first = store.upsert_user(_identity("a", "a@example.org"))
    second = store.upsert_user(_identity("b", "b@example.org"))

    assert CODE_PATTERN.match(first["participant_code"])
    assert CODE_PATTERN.match(second["participant_code"])
    assert first["participant_code"] != second["participant_code"]
    # A returning login keeps the same code.
    assert store.upsert_user(_identity("a", "a@example.org"))["participant_code"] == (
        first["participant_code"]
    )


def test_file_window_removes_files_and_contact_but_keeps_the_interaction():
    store = new_pilot_store()
    user = store.upsert_user(_identity())
    conversation_id, reservation, _ = _completed_turn(store, user["id"])
    _age_everything(store, 60)
    storage = _RecordingStorage()

    paths = purge_expired_content(
        store, 30, storage, research_retention_days=365
    )

    assert paths == ["users/u/old.jpg"]
    assert storage.deleted == ["users/u/old.jpg"]
    kept = store.get_user(user["id"])
    assert kept["email"] is None
    assert kept["name"] == user["participant_code"]
    messages = store.list_messages(user["id"], conversation_id)
    assert sorted(message["role"] for message in messages) == ["assistant", "user"]
    with store._connect() as connection:
        attachments = json.loads(
            connection.execute(
                "SELECT attachments_json FROM messages WHERE id = %s",
                (reservation.user_message_id,),
            ).fetchone()["attachments_json"]
        )
        linked = connection.execute(
            "SELECT count(*) AS n FROM query_events WHERE user_id = %s",
            (user["id"],),
        ).fetchone()["n"]
    assert attachments == [{"kind": "image", "mime_type": "image/jpeg", "expired": True}]
    assert linked == 1

    # A second run finds nothing left to delete from storage.
    assert purge_expired_content(store, 30, storage, research_retention_days=365) == []


def test_research_window_end_deletes_the_interaction_record():
    store = new_pilot_store()
    user = store.upsert_user(_identity())
    _, _, assistant_message_id = _completed_turn(store, user["id"])
    store.record_feedback(
        category="helpful",
        comment="Clear answer",
        consent=True,
        user_id=user["id"],
        message_id=assistant_message_id,
        rating=5,
    )
    _age_everything(store, 400)

    purge_expired_content(store, 30, _RecordingStorage(), research_retention_days=365)

    with store._connect() as connection:
        counts = {
            table: connection.execute(f"SELECT count(*) AS n FROM {table}").fetchone()["n"]
            for table in ("users", "conversations", "messages", "assistant_turns")
        }
        event = connection.execute("SELECT user_id FROM query_events").fetchone()
        feedback = connection.execute(
            "SELECT user_id, message_id, rating FROM feedback"
        ).fetchone()
    assert counts == {"users": 0, "conversations": 0, "messages": 0, "assistant_turns": 0}
    assert event["user_id"] is None
    assert feedback["user_id"] is None and feedback["message_id"] is None
    assert feedback["rating"] == 5


def test_returning_participant_regains_contact_details_and_history():
    store = new_pilot_store()
    user = store.upsert_user(_identity())
    conversation_id, _, _ = _completed_turn(store, user["id"])
    _age_everything(store, 60)
    purge_expired_content(store, 30, _RecordingStorage(), research_retention_days=365)

    returned = store.upsert_user(_identity())

    assert returned["id"] == user["id"]
    assert returned["email"] == "farmer@example.org"
    assert returned["name"] == "Farmer"
    assert returned["participant_code"] == user["participant_code"]
    assert len(store.list_messages(user["id"], conversation_id)) == 2


def test_research_window_shorter_than_file_window_is_rejected():
    store = new_pilot_store()
    with pytest.raises(ValueError, match="Research retention"):
        purge_expired_content(store, 30, research_retention_days=10)


def test_account_deletion_still_erases_the_research_record():
    store = new_pilot_store()
    user = store.upsert_user(_identity())
    _completed_turn(store, user["id"])

    store.delete_user_records(user["id"])

    dataset = build_research_dataset(store)
    assert dataset["participants"] == []
    assert dataset["interactions"] == []
    assert all(row["participant_code"] is None for row in dataset["query_events"])


def test_research_dataset_is_keyed_by_code_without_contact_details():
    store = new_pilot_store()
    user = store.upsert_user(_identity())
    _, _, assistant_message_id = _completed_turn(store, user["id"])
    store.record_feedback(
        category="helpful",
        comment="Clear answer",
        consent=True,
        user_id=user["id"],
        message_id=assistant_message_id,
        rating=4,
    )

    dataset = build_research_dataset(store)

    code = user["participant_code"]
    assert dataset["participants"][0]["participant_code"] == code
    assert dataset["participants"][0]["channel"] == "web"
    interaction = dataset["interactions"][0]
    assert interaction["participant_code"] == code
    assert interaction["question"] == "When should I prune olives?"
    assert interaction["answer"] == "Prune after harvest, before spring growth."
    assert interaction["domain"] == "olive"
    assert interaction["citation_count"] == 1
    assert dataset["query_events"][0]["participant_code"] == code
    assert dataset["feedback"][0]["rating"] == 4
    serialized = json.dumps(dataset, default=str)
    for identifier in ("farmer@example.org", "Farmer\"", user["id"], "subject"):
        assert identifier not in serialized
