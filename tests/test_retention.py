from farmers_chatbot.auth import UserIdentity
from farmers_chatbot.pilot_store import PilotStore
from farmers_chatbot.retention import purge_expired_content


def test_retention_deletes_content_and_anonymizes_metrics(tmp_path):
    store = PilotStore(sqlite_path=tmp_path / "pilot.sqlite3")
    user = store.upsert_user(
        UserIdentity(
            user_id="",
            issuer="test",
            subject="subject",
            email="tester@example.org",
            name="Tester",
            is_admin=False,
        )
    )
    conversation_id = store.create_conversation(user["id"])
    attachment_path = (
        f"users/{user['id']}/conversations/{conversation_id}/images/old.jpg"
    )
    store.add_message(
        user["id"],
        conversation_id,
        role="user",
        content="Old message",
        attachments=[{"kind": "image", "storage_path": attachment_path}],
    )
    assert store.check_rate_limit(user["id"]).allowed

    old = "2020-01-01T00:00:00+00:00"
    with store._connect() as connection:
        connection.execute(
            "UPDATE messages SET created_at = ? WHERE conversation_id = ?",
            (old, conversation_id),
        )
        connection.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (old, conversation_id),
        )
        connection.execute(
            "UPDATE query_events SET occurred_at = ?, day_utc = ?",
            (old, "2020-01-01"),
        )

    paths = purge_expired_content(store, 30)
    assert attachment_path in paths
    with store._connect() as connection:
        query_event = connection.execute(
            "SELECT user_id FROM query_events LIMIT 1"
        ).fetchone()
    assert query_event["user_id"] is None
