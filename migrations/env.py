"""Alembic environment for the managed PostgreSQL database."""

from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# RAISE uses SQL migrations and has no SQLAlchemy declarative metadata.
target_metadata = None


def _database_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if not url.startswith(("postgres://", "postgresql://")):
        raise RuntimeError(
            "Alembic requires DATABASE_URL to reference PostgreSQL; "
            "SQLite remains a development-only bootstrap."
        )
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    # SQLAlchemy otherwise defaults to psycopg2 for a plain PostgreSQL URL.
    return "postgresql+psycopg://" + url[len("postgresql://") :]


def run_migrations_offline() -> None:
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        transaction_per_migration=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = _database_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            transaction_per_migration=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
