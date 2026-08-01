"""Fail-closed validation for hosted pilot configuration."""

from __future__ import annotations

import os

from .config import (
    ACCESS_POLICY,
    ADMIN_EMAILS,
    AGREEMENT_TEXT_VERSION,
    ALLOWED_DOMAINS,
    ALLOWED_EMAILS,
    APP_DISPLAY_NAME,
    APP_ENV,
    APP_PUBLIC_URL,
    AUTH_MODE,
    CONSENT_VERSION,
    DATABASE_URL,
    DEFAULT_DEEP_MODEL,
    DEFAULT_FAST_MODEL,
    OPENROUTER_ALLOWED_MODELS,
    OPENROUTER_DATA_COLLECTION,
    OPENROUTER_DEFAULT_MODEL,
    OPENROUTER_ENFORCE_ZDR,
    OPENROUTER_UNKNOWN_MODELS,
    ORGANIZATION_NAME,
    PRIVACY_CONTACT_EMAIL,
    RETENTION_DAYS,
    SUPABASE_SERVICE_ROLE_KEY,
    SUPABASE_STORAGE_BUCKET,
    SUPABASE_URL,
)


def validate_web_runtime() -> None:
    """Reject an unsafe hosted pilot that would fall back to local state."""

    if APP_ENV != "pilot":
        return
    missing = []
    if AUTH_MODE != "google":
        missing.append("AUTH_MODE=google")
    if not APP_PUBLIC_URL.startswith("https://"):
        missing.append("APP_PUBLIC_URL (HTTPS)")
    if ACCESS_POLICY not in {
        "google_any",
        "email_allowlist",
        "domain_allowlist",
    }:
        missing.append("ACCESS_POLICY")
    if ACCESS_POLICY == "email_allowlist" and not ALLOWED_EMAILS:
        missing.append("ALLOWED_EMAILS")
    if ACCESS_POLICY == "domain_allowlist" and not ALLOWED_DOMAINS:
        missing.append("ALLOWED_DOMAINS")
    if not ADMIN_EMAILS:
        missing.append("ADMIN_EMAILS")
    if not DATABASE_URL.startswith(("postgres://", "postgresql://")):
        missing.append("DATABASE_URL (PostgreSQL)")
    if not SUPABASE_URL:
        missing.append("SUPABASE_URL")
    if not SUPABASE_SERVICE_ROLE_KEY:
        missing.append("SUPABASE_SERVICE_ROLE_KEY")
    if not SUPABASE_STORAGE_BUCKET:
        missing.append("SUPABASE_STORAGE_BUCKET")
    if not os.getenv("OPENROUTER_API_KEY"):
        missing.append("OPENROUTER_API_KEY")
    if OPENROUTER_UNKNOWN_MODELS:
        missing.append("OPENROUTER_ALLOWED_MODELS (contains unsupported IDs)")
    if OPENROUTER_DEFAULT_MODEL not in OPENROUTER_ALLOWED_MODELS:
        missing.append("OPENROUTER_DEFAULT_MODEL (must be allowed)")
    if DEFAULT_FAST_MODEL not in OPENROUTER_ALLOWED_MODELS:
        missing.append("OPENROUTER_FAST_MODEL (must be allowed)")
    if DEFAULT_DEEP_MODEL not in OPENROUTER_ALLOWED_MODELS:
        missing.append("OPENROUTER_DEEP_MODEL (must be allowed)")
    if not OPENROUTER_ENFORCE_ZDR:
        missing.append("OPENROUTER_ENFORCE_ZDR=true")
    if OPENROUTER_DATA_COLLECTION != "deny":
        missing.append("OPENROUTER_DATA_COLLECTION=deny")
    if not ORGANIZATION_NAME:
        missing.append("ORGANIZATION_NAME")
    if not APP_DISPLAY_NAME:
        missing.append("APP_DISPLAY_NAME")
    if CONSENT_VERSION != AGREEMENT_TEXT_VERSION:
        missing.append(
            f"CONSENT_VERSION={AGREEMENT_TEXT_VERSION} (must match deployed text)"
        )
    if (
        "@" not in PRIVACY_CONTACT_EMAIL
        or PRIVACY_CONTACT_EMAIL.endswith(".invalid")
    ):
        missing.append("PRIVACY_CONTACT_EMAIL")
    if RETENTION_DAYS < 1 or RETENTION_DAYS > 30:
        missing.append("RETENTION_DAYS (1-30)")
    if missing:
        raise RuntimeError(
            "Unsafe pilot configuration; required managed settings are missing: "
            + ", ".join(missing)
        )
