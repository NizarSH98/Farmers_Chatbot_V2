# Database migrations

RAISE uses Alembic for every managed PostgreSQL schema change. Application
startup verifies the exact expected revision and never creates or alters hosted
tables. SQLite schema bootstrap remains available only for local development and
tests.

## First Alembic adoption

Revision `20260811_0001` adopts the previously deployed `001` and `002` SQL
schemas. The SQL is idempotent and checksum-pinned. On an existing database the
upgrade preserves records, adds only any missing legacy objects, and then records
the Alembic revision. On a new database it creates the same schema.

Before adopting an existing pilot database:

1. Stop writes or enter a maintenance window.
2. Create a provider-level PostgreSQL backup and verify its completion.
3. Export private storage and database records using
   `scripts/pilot_data_portability.py`; retain the manifest and checksums.
4. Restore both backups into a disposable environment and verify users, consent,
   conversations, projects, documents, artifacts, feedback, usage events, and
   referenced private objects.
5. Point `DATABASE_URL` at the target and run `alembic upgrade head`.
6. Run `alembic current --check` and start the service only after it succeeds.

Never use `alembic stamp` for initial adoption: it would skip the idempotent schema
verification performed by the baseline.

## Normal deployment

Create one immutable revision for each schema change:

```text
alembic revision -m "short description"
alembic upgrade head
alembic current --check
```

Render executes `alembic upgrade head` as a pre-deploy command. If migration fails,
the new service version must not start. The application then independently checks
the `alembic_version` table during readiness validation.

Do not modify `001_pilot_schema.sql`, `002_web_platform.sql`, or an applied Alembic
revision. Add a new revision instead. Update
`farmers_chatbot.migration_status.EXPECTED_DATABASE_REVISION` whenever the single
Alembic head changes.

## Rollback

Take a fresh backup before every migration. Test both upgrade and downgrade against
a restored copy containing representative pilot records. A revision downgrade must
preserve records unless the release procedure explicitly authorizes a destructive
data migration.

The adoption baseline's downgrade intentionally removes only Alembic's revision
marker; it never drops legacy tables. Reapplying the baseline safely adopts the
unchanged schema again.

## Local development

Local SQLite databases continue to initialize on `PilotStore` construction and do
not use Alembic. Use a disposable PostgreSQL database when developing or testing a
PostgreSQL-specific revision.
