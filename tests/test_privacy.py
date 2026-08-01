import pytest

from farmers_chatbot.auth import UserIdentity
from farmers_chatbot.documents import DocumentService
from farmers_chatbot.legal import (
    LEGAL_ROOT,
    agreement_markdown,
    agreement_markdown_ar,
    privacy_policy_markdown,
    privacy_policy_markdown_ar,
)
from farmers_chatbot.pilot_store import PilotStore
from farmers_chatbot.storage_backends import LocalPrivateStorage


def test_versioned_notice_is_bilingual_and_names_processing_boundaries():
    english = agreement_markdown()
    arabic = agreement_markdown_ar()
    privacy = privacy_policy_markdown()
    privacy_ar = privacy_policy_markdown_ar()
    assert "OpenRouter" in privacy
    assert "Supabase" in privacy
    assert "delete your account" in english
    assert "project lifecycle" in english
    assert "DRAFT" in english
    assert "legal data controller" in privacy
    assert "simultaneous users" not in privacy
    assert "{{" not in f"{english}{arabic}{privacy}{privacy_ar}"
    assert "الخصوصية" in privacy_ar
    assert "الاستخدام" in arabic


def test_lifecycle_legal_documents_are_reviewable_source_files():
    expected = {
        "USER_AGREEMENT.en.md",
        "USER_AGREEMENT.ar.md",
        "PRIVACY_POLICY.en.md",
        "PRIVACY_POLICY.ar.md",
    }
    assert expected == {path.name for path in LEGAL_ROOT.glob("*.md")}
    for filename in expected:
        source = (LEGAL_ROOT / filename).read_text(encoding="utf-8")
        assert "{{LEGAL_VERSION}}" in source
        assert "DRAFT" in source or "مسودة" in source


def test_user_can_export_and_delete_identity_and_private_content(tmp_path):
    store = PilotStore(sqlite_path=tmp_path / "pilot.sqlite3")
    storage = LocalPrivateStorage(tmp_path / "private")
    user = store.upsert_user(
        UserIdentity(
            user_id="",
            issuer="https://accounts.google.com",
            subject="private-subject",
            email="tester@example.org",
            name="Tester",
            is_admin=False,
        )
    )
    store.accept_consent(user["id"])
    project_id = store.create_project(user["id"], "Private project")
    documents = DocumentService(store, storage)
    documents.ingest(
        user["id"],
        project_id,
        filename="notes.txt",
        data=b"Non-sensitive field notes",
        mime_type="text/plain",
    )
    conversation_id = store.create_conversation(
        user["id"], project_id=project_id
    )
    image_path = (
        f"users/{user['id']}/conversations/{conversation_id}/images/test.jpg"
    )
    storage.put(image_path, b"test", "image/jpeg")
    store.add_message(
        user["id"],
        conversation_id,
        role="user",
        content="My question",
        attachments=[{"kind": "image", "storage_path": image_path}],
    )
    assert store.check_rate_limit(user["id"]).allowed

    exported = store.export_user_data(user["id"])
    assert exported["user"]["email"] == "tester@example.org"
    assert exported["messages"][0]["content"] == "My question"
    paths = store.user_storage_paths(user["id"])
    assert image_path in paths
    for path in paths:
        storage.delete(path)
    store.delete_user_records(user["id"])

    with pytest.raises(ValueError, match="User not found"):
        store.get_user(user["id"])
    with store._connect() as connection:
        event = connection.execute(
            "SELECT user_id FROM query_events LIMIT 1"
        ).fetchone()
    assert event["user_id"] is None
    for path in paths:
        with pytest.raises(FileNotFoundError):
            storage.get(path)
