# Pilot Data Portability and Exit Procedure

The pilot stores application records in standard PostgreSQL and private file
objects behind the `PrivateFileStorage` interface. Supabase Auth, Realtime, Edge
Functions, and database-specific application APIs are not required. This limits
lock-in, but ownership still requires tested exports and custody of the backups.

## Security rules

- Run exports only from a trusted administrator machine while no pilot write
  activity is occurring.
- Treat the entire export as sensitive personal data. Keep it outside Git,
  shared chat, ordinary email, and unencrypted removable storage.
- Store it in institution-approved encrypted storage with access logging and a
  deletion date. Never publish `manifest.json`; object paths contain internal IDs.
- Pass database credentials through environment variables, not command arguments.
- Verify every export immediately and perform a restore rehearsal before the pilot.

`pilot_exports/` is ignored for local rehearsals, but an institution-controlled
directory outside the repository is preferred.

## Prerequisites

Install PostgreSQL client tools matching the source server major version closely
enough to provide `pg_dump` and `pg_restore`. The application Python environment
must also be active.

For a hosted PostgreSQL source, keep the application pooler URL in `DATABASE_URL`
and temporarily set `DATABASE_EXPORT_URL` to the provider's direct connection URL.
The export script passes parsed credentials to `pg_dump` through `PG*` process
environment variables and never writes the connection URL into the manifest.

## Create and verify an export

PowerShell example:

```powershell
$env:DATABASE_EXPORT_URL = 'postgresql://USER:PASSWORD@DIRECT_HOST:5432/postgres?sslmode=require'
python scripts/pilot_data_portability.py export --output-dir 'D:\secure-pilot-backups\pilot-2026-08-05'
Remove-Item Env:DATABASE_EXPORT_URL
python scripts/pilot_data_portability.py verify --input-dir 'D:\secure-pilot-backups\pilot-2026-08-05'
```

The directory contains:

- `database.dump`, a provider-neutral PostgreSQL custom-format dump;
- `objects/`, with original provider-neutral storage paths preserved;
- `manifest.json`, containing sizes and SHA-256 hashes but no credentials.

The same command creates `database.sqlite3` for a local SQLite rehearsal. Do not
use `--skip-database` for a formal backup.

## Restore the database to a new provider

Create a new, empty PostgreSQL database owned by the application role. Use
connection environment variables appropriate to the new provider and restore the
custom dump without provider ownership or privilege statements:

```powershell
$env:PGHOST = 'TARGET_HOST'
$env:PGPORT = '5432'
$env:PGDATABASE = 'TARGET_EMPTY_DATABASE'
$env:PGUSER = 'TARGET_USER'
$env:PGPASSWORD = 'TARGET_PASSWORD'
$env:PGSSLMODE = 'require'
pg_restore --exit-on-error --no-owner --no-privileges --dbname TARGET_EMPTY_DATABASE 'D:\secure-pilot-backups\pilot-2026-08-05\database.dump'
Remove-Item Env:PGPASSWORD
```

Never restore over the active pilot database. Restore into a separate empty
database, apply any newer repository migrations, and validate counts and ownership
isolation before changing application secrets.

## Restore files to a new backend

Configure the target backend through environment variables. With a new private
Supabase bucket this means `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, and
`SUPABASE_STORAGE_BUCKET`. Then run:

```powershell
python scripts/pilot_data_portability.py restore-files --input-dir 'D:\secure-pilot-backups\pilot-2026-08-05' --write-files
```

The restore verifies the complete export first. It writes only missing objects,
skips byte-identical objects, refuses to overwrite different content, and verifies
each object after upload. A future S3-compatible adapter can implement the existing
four-method storage interface without changing database object paths.

## Cutover and rollback

1. Freeze writes and take a final verified source export.
2. Restore into a new empty PostgreSQL database and private bucket.
3. Run migration, two-user isolation, download, deletion, retention, and artifact
   checks against a non-public candidate deployment.
4. Change managed secrets only after the checks pass.
5. Keep the old service read-only during the agreed rollback window.
6. Record source/target providers, regions, timestamps, manifest hash, operator,
   reviewer, application commit, and deletion date.
7. Delete old provider data only after written owner approval and verified cutover.
