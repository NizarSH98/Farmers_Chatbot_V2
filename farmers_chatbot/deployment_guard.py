"""Fail-closed validation for hosted pilot configuration."""

from __future__ import annotations

import os

from .config import (
    APP_ENV,
    AUTH_MODE,
    DATABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY,
    SUPABASE_URL,
)


def validate_web_runtime() -> None:
    """Reject an unsafe hosted pilot that would fall back to local state."""

    if APP_ENV != "pilot":
        return
    missing = []
    if AUTH_MODE != "google":
        missing.append("AUTH_MODE=google")
    if not DATABASE_URL.startswith(("postgres://", "postgresql://")):
        missing.append("DATABASE_URL (PostgreSQL)")
    if not SUPABASE_URL:
        missing.append("SUPABASE_URL")
    if not SUPABASE_SERVICE_ROLE_KEY:
        missing.append("SUPABASE_SERVICE_ROLE_KEY")
    if not os.getenv("OPENROUTER_API_KEY"):
        missing.append("OPENROUTER_API_KEY")
    if missing:
        raise RuntimeError(
            "Unsafe pilot configuration; required managed settings are missing: "
            + ", ".join(missing)
        )
