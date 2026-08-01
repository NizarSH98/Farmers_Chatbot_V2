'''Export, verify, and restore pilot data without Supabase-specific formats.'''

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from farmers_chatbot.pilot_store import PilotStore
from farmers_chatbot.storage_backends import (
    PrivateFileStorage,
    configured_file_storage,
    safe_storage_path,
)

FORMAT_VERSION = 1


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_backup_path(root: Path, storage_path: str) -> Path:
    relative = Path('objects') / Path(safe_storage_path(storage_path))
    target = (root / relative).resolve()
    resolved_root = root.resolve()
    if resolved_root not in target.parents:
        raise ValueError('Unsafe object path in portability manifest')
    return target


def _postgres_environment(database_url: str) -> tuple[dict[str, str], str]:
    parsed = urlsplit(database_url)
    if parsed.scheme not in {'postgres', 'postgresql'}:
        raise ValueError('A PostgreSQL URL is required for pg_dump')
    database = unquote(parsed.path.lstrip('/'))
    if not parsed.hostname or not database:
        raise ValueError('PostgreSQL URL is missing a host or database name')
    environment = os.environ.copy()
    environment.update(
        {
            'PGHOST': parsed.hostname,
            'PGPORT': str(parsed.port or 5432),
            'PGDATABASE': database,
        }
    )
    if parsed.username:
        environment['PGUSER'] = unquote(parsed.username)
    if parsed.password:
        environment['PGPASSWORD'] = unquote(parsed.password)
    sslmode = parse_qs(parsed.query).get('sslmode', [None])[0]
    if sslmode:
        environment['PGSSLMODE'] = sslmode
    return environment, database


def _dump_postgres(database_url: str, target: Path) -> None:
    executable = os.getenv('PG_DUMP_BIN', 'pg_dump')
    resolved = shutil.which(executable)
    if not resolved:
        raise RuntimeError(
            'pg_dump is not installed or PG_DUMP_BIN does not point to it'
        )
    environment, database = _postgres_environment(database_url)
    result = subprocess.run(
        [
            resolved,
            '--format=custom',
            '--no-owner',
            '--no-privileges',
            '--file',
            str(target),
            database,
        ],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )
    if result.returncode:
        detail = (result.stderr or 'pg_dump failed').strip()[-1000:]
        raise RuntimeError(f'PostgreSQL export failed: {detail}')


def _dump_sqlite(source: Path, target: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError('Local SQLite pilot database was not found')
    source_connection = sqlite3.connect(f'file:{source.resolve()}?mode=ro', uri=True)
    target_connection = sqlite3.connect(target)
    try:
        source_connection.backup(target_connection)
    finally:
        target_connection.close()
        source_connection.close()


def export_backup(
    output_dir: Path,
    store: PilotStore,
    storage: PrivateFileStorage,
    *,
    include_database: bool = True,
    database_dump_url: str = '',
) -> dict:
    '''Create a portable database/file export and integrity manifest.'''

    output_dir = output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError('Export directory must be new or empty')
    output_dir.mkdir(parents=True, exist_ok=True)
    objects: list[dict] = []
    errors: list[str] = []

    for record in store.storage_inventory():
        storage_path = str(record['storage_path'])
        target = _safe_backup_path(output_dir, storage_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            data = storage.get(storage_path)
            digest = _sha256(data)
            expected_hash = record.get('expected_sha256')
            expected_size = record.get('expected_size_bytes')
            if expected_hash and digest != expected_hash:
                errors.append(f'Hash mismatch for {storage_path}')
            if expected_size is not None and len(data) != int(expected_size):
                errors.append(f'Size mismatch for {storage_path}')
            target.write_bytes(data)
            objects.append(
                {
                    'storage_path': storage_path,
                    'backup_path': target.relative_to(output_dir).as_posix(),
                    'kind': record['kind'],
                    'mime_type': record['mime_type'],
                    'size_bytes': len(data),
                    'sha256': digest,
                }
            )
        except Exception as exc:  # noqa: BLE001 - report every missing object
            errors.append(f'Could not export {storage_path}: {type(exc).__name__}')

    database: dict | None = None
    if include_database:
        if store.is_postgres:
            dump_path = output_dir / 'database.dump'
            _dump_postgres(database_dump_url or store.database_url, dump_path)
            database = {
                'engine': 'postgresql',
                'backup_path': dump_path.name,
                'format': 'pg_dump-custom',
                'size_bytes': dump_path.stat().st_size,
                'sha256': _sha256_file(dump_path),
            }
        else:
            dump_path = output_dir / 'database.sqlite3'
            _dump_sqlite(store.sqlite_path, dump_path)
            database = {
                'engine': 'sqlite',
                'backup_path': dump_path.name,
                'format': 'sqlite-backup',
                'size_bytes': dump_path.stat().st_size,
                'sha256': _sha256_file(dump_path),
            }

    manifest = {
        'format': 'raise-esdu-pilot-portability',
        'format_version': FORMAT_VERSION,
        'created_at': datetime.now(UTC).isoformat(),
        'contains_personal_data': True,
        'database': database,
        'object_count': len(objects),
        'objects': objects,
        'errors': errors,
    }
    (output_dir / 'manifest.json').write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )
    if errors:
        raise RuntimeError(
            'Portability export was incomplete; inspect manifest.json and do not '
            'treat the backup as valid'
        )
    return manifest


def verify_backup(input_dir: Path) -> list[str]:
    '''Return integrity errors for an export without changing any data.'''

    input_dir = input_dir.resolve()
    manifest_path = input_dir / 'manifest.json'
    if not manifest_path.is_file():
        return ['manifest.json is missing']
    try:
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return ['manifest.json is unreadable']
    errors: list[str] = []
    if manifest.get('format') != 'raise-esdu-pilot-portability':
        errors.append('Unknown portability format')
    if manifest.get('format_version') != FORMAT_VERSION:
        errors.append('Unsupported portability format version')
    errors.extend(str(error) for error in manifest.get('errors', []))

    database = manifest.get('database')
    if database:
        database_path = (input_dir / str(database.get('backup_path', ''))).resolve()
        if input_dir not in database_path.parents or not database_path.is_file():
            errors.append('Database backup is missing or unsafe')
        else:
            if database_path.stat().st_size != int(database.get('size_bytes', -1)):
                errors.append('Database backup size does not match the manifest')
            if _sha256_file(database_path) != database.get('sha256'):
                errors.append('Database backup hash does not match the manifest')

    objects = manifest.get('objects', [])
    if manifest.get('object_count') != len(objects):
        errors.append('Object count does not match the manifest')
    for record in objects:
        storage_path = str(record.get('storage_path', ''))
        try:
            expected_path = _safe_backup_path(input_dir, storage_path)
        except ValueError:
            errors.append(f'Unsafe storage path: {storage_path}')
            continue
        expected_relative = expected_path.relative_to(input_dir).as_posix()
        if record.get('backup_path') != expected_relative:
            errors.append(f'Backup path mismatch for {storage_path}')
            continue
        if not expected_path.is_file():
            errors.append(f'Exported object is missing: {storage_path}')
            continue
        if expected_path.stat().st_size != int(record.get('size_bytes', -1)):
            errors.append(f'Exported object size mismatch: {storage_path}')
        if _sha256_file(expected_path) != record.get('sha256'):
            errors.append(f'Exported object hash mismatch: {storage_path}')
    return errors


def restore_private_files(
    input_dir: Path,
    storage: PrivateFileStorage,
) -> dict[str, int]:
    '''Restore missing private objects and refuse to overwrite different data.'''

    errors = verify_backup(input_dir)
    if errors:
        raise ValueError('Backup verification failed: ' + '; '.join(errors))
    input_dir = input_dir.resolve()
    manifest = json.loads((input_dir / 'manifest.json').read_text(encoding='utf-8'))
    restored = 0
    skipped = 0
    for record in manifest['objects']:
        storage_path = str(record['storage_path'])
        source = _safe_backup_path(input_dir, storage_path)
        data = source.read_bytes()
        try:
            existing = storage.get(storage_path)
        except FileNotFoundError:
            existing = None
        if existing is not None:
            if _sha256(existing) != record['sha256']:
                raise RuntimeError(
                    f'Refusing to overwrite different target object: {storage_path}'
                )
            skipped += 1
            continue
        storage.put(storage_path, data, str(record['mime_type']))
        try:
            restored_data = storage.get(storage_path)
            if _sha256(restored_data) != record['sha256']:
                raise RuntimeError(f'Restored object failed verification: {storage_path}')
        except Exception:  # noqa: BLE001 - delete any unverified restored object
            try:
                storage.delete(storage_path)
            finally:
                raise
        restored += 1
    return {'restored': restored, 'skipped_matching': skipped}


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Export, verify, or restore RAISE pilot data.'
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    export_parser = subparsers.add_parser('export')
    export_parser.add_argument('--output-dir', type=Path, required=True)
    export_parser.add_argument('--skip-database', action='store_true')
    export_parser.add_argument(
        '--database-url-env',
        default='DATABASE_EXPORT_URL',
        help='Environment variable holding the direct pg_dump URL.',
    )

    verify_parser = subparsers.add_parser('verify')
    verify_parser.add_argument('--input-dir', type=Path, required=True)

    restore_parser = subparsers.add_parser('restore-files')
    restore_parser.add_argument('--input-dir', type=Path, required=True)
    restore_parser.add_argument(
        '--write-files',
        action='store_true',
        help='Required confirmation that the configured target may receive files.',
    )

    args = parser.parse_args()
    if args.command == 'verify':
        errors = verify_backup(args.input_dir)
        if errors:
            print('Portability verification failed:')
            for error in errors:
                print(f'- {error}')
            return 1
        print('Portability verification passed.')
        return 0

    if args.command == 'restore-files':
        if not args.write_files:
            raise SystemExit('restore-files requires --write-files')
        result = restore_private_files(args.input_dir, configured_file_storage())
        print(
            f'''Private-file restore passed: restored={result['restored']}, '''
            f'''skipped_matching={result['skipped_matching']}'''
        )
        return 0

    store = PilotStore()
    export_url = os.getenv(args.database_url_env, '')
    manifest = export_backup(
        args.output_dir,
        store,
        configured_file_storage(),
        include_database=not args.skip_database,
        database_dump_url=export_url,
    )
    database_status = 'included' if manifest['database'] else 'skipped'
    print(
        f'''Portable export passed: objects={manifest['object_count']}, '''
        f'database={database_status}'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
