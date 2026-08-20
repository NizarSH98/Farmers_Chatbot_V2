"""The v2 rollout archives prior workspace content and keeps accounts."""

from __future__ import annotations

import json

from conftest import new_pilot_store

from scripts.archive_user_data import archive


def _seed(store):
    user = store.upsert_supabase_user(
        auth_user_id="auth-archive-1",
        email="farmer@example.org",
        name="Farmer",
        google_subject=None,
        is_admin=False,
    )
    conversation_id = store.create_conversation(user["id"], title="Old season")
    store.add_message(
        user["id"],
        conversation_id,
        role="user",
        content="How much water did I use?",
    )
    return user


def test_archive_writes_checksummed_exports_and_keeps_accounts(tmp_path):
    store = new_pilot_store()
    try:
        user = _seed(store)
        manifest = archive(store, tmp_path, purge=False)

        assert manifest["user_count"] == 1
        assert manifest["purged"] is False
        entry = manifest["users"][0]
        exported = json.loads((tmp_path / entry["file"]).read_text(encoding="utf-8"))
        assert exported
        # Nothing is removed without --purge.
        assert store.list_conversations(user["id"])
    finally:
        store.close()


def test_purge_removes_content_but_leaves_the_registered_account(tmp_path):
    store = new_pilot_store()
    try:
        user = _seed(store)
        manifest = archive(store, tmp_path, purge=True)

        assert manifest["purged"] is True
        assert "conversations" in manifest["purged_tables"]
        assert "users" in manifest["retained_tables"]
        assert store.list_conversations(user["id"]) == []
        with store._connect() as connection:
            remaining = connection.execute(
                "SELECT COUNT(*) AS n FROM users"
            ).fetchone()["n"]
        assert remaining == 1
    finally:
        store.close()
