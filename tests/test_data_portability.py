import hashlib

from farmers_chatbot.auth import UserIdentity
from farmers_chatbot.pilot_store import PilotStore
from farmers_chatbot.storage_backends import LocalPrivateStorage
from scripts.pilot_data_portability import (
    export_backup,
    restore_private_files,
    verify_backup,
)


def test_export_verify_and_restore_preserves_database_and_private_files(tmp_path):
    store = PilotStore(sqlite_path=tmp_path / 'pilot.sqlite3')
    source_storage = LocalPrivateStorage(tmp_path / 'source-files')
    user = store.upsert_user(
        UserIdentity(
            user_id='',
            issuer='test',
            subject='subject',
            email='tester@example.org',
            name='Tester',
            is_admin=False,
        )
    )
    project_id = store.create_project(user['id'], 'Portable project')
    document_data = b'portable field notes'
    document_path = f'''users/{user['id']}/projects/{project_id}/notes.txt'''
    source_storage.put(document_path, document_data, 'text/plain')
    store.add_document(
        user['id'],
        project_id,
        filename='notes.txt',
        mime_type='text/plain',
        storage_path=document_path,
        sha256=hashlib.sha256(document_data).hexdigest(),
        size_bytes=len(document_data),
        chunks=['portable field notes'],
    )
    conversation_id = store.create_conversation(user['id'], project_id=project_id)
    image_path = f'''users/{user['id']}/conversations/{conversation_id}/field.jpg'''
    source_storage.put(image_path, b'image-bytes', 'image/jpeg')
    store.add_message(
        user['id'],
        conversation_id,
        role='user',
        content='Inspect this image',
        attachments=[
            {
                'kind': 'image',
                'mime_type': 'image/jpeg',
                'storage_path': image_path,
                'size_bytes': len(b'image-bytes'),
            }
        ],
    )

    export_dir = tmp_path / 'export'
    manifest = export_backup(export_dir, store, source_storage)

    assert manifest['database']['engine'] == 'sqlite'
    assert manifest['object_count'] == 2
    assert verify_backup(export_dir) == []

    target_storage = LocalPrivateStorage(tmp_path / 'target-files')
    first = restore_private_files(export_dir, target_storage)
    second = restore_private_files(export_dir, target_storage)
    assert first == {'restored': 2, 'skipped_matching': 0}
    assert second == {'restored': 0, 'skipped_matching': 2}
    assert target_storage.get(document_path) == document_data
    assert target_storage.get(image_path) == b'image-bytes'


def test_verifier_detects_changed_database_backup(tmp_path):
    store = PilotStore(sqlite_path=tmp_path / 'pilot.sqlite3')
    storage = LocalPrivateStorage(tmp_path / 'source-files')
    export_dir = tmp_path / 'export'
    export_backup(export_dir, store, storage)
    database_path = export_dir / 'database.sqlite3'
    database_path.write_bytes(database_path.read_bytes() + b'changed')

    assert 'Database backup size does not match' in ' '.join(
        verify_backup(export_dir)
    )
