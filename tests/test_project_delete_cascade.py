import pytest

from farmers_chatbot.artifacts import ArtifactService
from farmers_chatbot.auth import UserIdentity
from farmers_chatbot.pilot_store import PilotStore
from farmers_chatbot.storage_backends import LocalPrivateStorage


def test_project_deletion_removes_artifact_record_and_private_path(tmp_path):
    store = PilotStore(sqlite_path=tmp_path / "pilot.sqlite3")
    storage = LocalPrivateStorage(tmp_path / "private")
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
    project_id = store.create_project(user["id"], "Project")
    artifact = ArtifactService(
        store,
        storage,
        owner_user_id=user["id"],
        project_id=project_id,
    ).generate_inspection_checklist(
        title="Field check",
        context="Pilot",
        checks=["Check one"],
    )

    paths = store.delete_project(user["id"], project_id)
    assert paths
    with pytest.raises(ValueError):
        store.get_artifact(user["id"], artifact["artifact_id"])
