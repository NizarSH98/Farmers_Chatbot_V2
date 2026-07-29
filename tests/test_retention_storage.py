import pytest

from farmers_chatbot.auth import UserIdentity
from farmers_chatbot.pilot_store import PilotStore
from farmers_chatbot.retention import purge_expired_content


class _FailingStorage:
    @staticmethod
    def delete(path):
        del path
        raise RuntimeError("provider unavailable")


def test_retention_keeps_database_record_if_private_delete_fails(tmp_path):
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
    store.add_message(
        user["id"],
        conversation_id,
        role="user",
        content="Old message",
        attachments=[{"storage_path": "users/test/old.jpg"}],
    )
    with store._connect() as connection:
        connection.execute(
            "UPDATE messages SET created_at = ? WHERE conversation_id = ?",
            ("2020-01-01T00:00:00+00:00", conversation_id),
        )

    with pytest.raises(RuntimeError, match="provider unavailable"):
        purge_expired_content(store, 30, _FailingStorage())
    assert store.list_messages(user["id"], conversation_id)
