# Data portability and exit procedure

Application records are standard PostgreSQL. Private objects use a Docker named
volume or S3-compatible private bucket. Qdrant is rebuildable, not authoritative.

## Portable assets

- PostgreSQL custom dump made with `--no-owner --no-privileges`.
- Private-file tree with stable paths, or the private S3 bucket.
- Environment secret record held outside Git.
- Exact API, web, and backup image SHA tags.
- Repository Compose and Alembic revisions.

## Exit to another host

1. Freeze writes and complete an off-VPS backup.
2. Restore restic into an operator-only directory.
3. Restore PostgreSQL into a new PostgreSQL 16/pgvector database.
4. Restore private files to a new volume, or copy the private S3 bucket.
5. Deploy exact image SHA tags with the same non-secret configuration.
6. Run migrations, health, isolation, file, and smoke tests.
7. Switch DNS only after validation and keep the old deployment read-only
   during the rollback window.

Commands and the test-restore process are in [DEPLOYMENT.md](DEPLOYMENT.md).
