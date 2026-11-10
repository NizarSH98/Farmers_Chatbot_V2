# Database migrations

RAISE uses Alembic for every managed PostgreSQL schema change. There is no
SQLite runtime fallback. Fresh databases and upgrades use the same linear graph.

## Deployment behavior

`compose.yaml` has a one-shot `migrate` service:

```text
python -m alembic upgrade head
```

The API depends on successful completion. Database mutation is not hidden in
API startup. API readiness reports expected and applied revisions.

Current head: `20261110_0008`.

## Creating a revision

```text
alembic revision -m "short description"
alembic upgrade head
alembic current --check
```

Never edit an applied revision or checksum-pinned legacy SQL. Update
`farmers_chatbot.migration_status.EXPECTED_DATABASE_REVISION` whenever the
single head changes. Validate `alembic heads`, generate an offline upgrade,
then apply it to a disposable PostgreSQL database and run smoke tests.

## Backup and rollback

Verify an off-VPS backup before a schema deployment. Image rollback is simple
when no incompatible schema was applied. Otherwise restore the pre-deploy backup
into a new database/volume and deploy the matching prior SHA images. Do not
overwrite the live database or guess at a downgrade.

Revision `20260901_0007` removes the obsolete vendor-auth ID column. This
deployment is explicitly a fresh user-data reset, so no identity mapping is
required. Issuer and subject remain the provider-neutral identity key.

Revision `20261110_0008` adds `users.participant_code`, a unique pseudonymous
code such as `RAISE-7K3QX9`, and backfills existing accounts. It is the key of
the research interaction record; see
[DATA_RETENTION_AND_RESEARCH.md](DATA_RETENTION_AND_RESEARCH.md).
