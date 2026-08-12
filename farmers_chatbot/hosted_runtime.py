"""Fail-closed validation for hosted RAISE service configuration."""

from __future__ import annotations

from collections.abc import Callable
from urllib.parse import urlparse

from .config import MODEL_CATALOG
from .migration_status import require_database_revision
from .runtime_settings import RuntimeSettings
from .trusted_sources import validate_live_source_registry

RevisionChecker = Callable[[str], str]


def _is_https_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


def _valid_email(value: str) -> bool:
    local, separator, domain = value.rpartition("@")
    return bool(local and separator and "." in domain) and not domain.endswith(
        ".invalid"
    )


def _common_issues(settings: RuntimeSettings) -> list[str]:
    issues: list[str] = []
    if settings.schema_version != "raise-runtime-v1":
        issues.append("runtime settings schema version")
    if not _is_https_url(settings.app_public_url):
        issues.append("APP_PUBLIC_URL (HTTPS)")
    if not settings.app_display_name:
        issues.append("APP_DISPLAY_NAME")
    if not settings.organization_name:
        issues.append("ORGANIZATION_NAME")
    if not _valid_email(settings.privacy_contact_email):
        issues.append("PRIVACY_CONTACT_EMAIL")
    if settings.consent_version != settings.agreement_text_version:
        issues.append(
            f"CONSENT_VERSION={settings.agreement_text_version} "
            "(must match deployed text)"
        )
    if settings.retention_days is None or not 1 <= settings.retention_days <= 30:
        issues.append("RETENTION_DAYS (1-30)")
    if not settings.database_url.startswith(("postgres://", "postgresql://")):
        issues.append("DATABASE_URL (PostgreSQL)")
    if not _is_https_url(settings.supabase_url):
        issues.append("SUPABASE_URL (HTTPS)")
    if not settings.supabase_service_role_key:
        issues.append("SUPABASE_SERVICE_ROLE_KEY")
    if not settings.supabase_storage_bucket:
        issues.append("SUPABASE_STORAGE_BUCKET")
    if not settings.openrouter_api_key:
        issues.append("OPENROUTER_API_KEY")
    if not _is_https_url(settings.openrouter_api_url):
        issues.append("OPENROUTER_API_URL (HTTPS)")

    supported_models = frozenset(MODEL_CATALOG)
    unknown_models = set(settings.openrouter_allowed_models) - supported_models
    if unknown_models:
        issues.append("OPENROUTER_ALLOWED_MODELS (contains unsupported IDs)")
    if not settings.openrouter_allowed_models:
        issues.append("OPENROUTER_ALLOWED_MODELS")
    required_models = {
        "OPENROUTER_DEFAULT_MODEL": settings.openrouter_default_model,
        "OPENROUTER_FAST_MODEL": settings.openrouter_fast_model,
        "OPENROUTER_DEEP_MODEL": settings.openrouter_deep_model,
        "REQUEST_ANALYZER_MODEL": settings.request_analyzer_model,
        "ANSWER_VERIFIER_MODEL": settings.answer_verifier_model,
    }
    allowed_models = set(settings.openrouter_allowed_models)
    for name, model_id in required_models.items():
        if not model_id or model_id not in allowed_models:
            issues.append(f"{name} (must be allowed)")
    if not settings.openrouter_enforce_zdr:
        issues.append("OPENROUTER_ENFORCE_ZDR=true")
    if settings.openrouter_data_collection != "deny":
        issues.append("OPENROUTER_DATA_COLLECTION=deny")
    if settings.trusted_search_enabled:
        try:
            validate_live_source_registry(
                settings.live_source_registry_path,
                require_authorized=True,
            )
        except RuntimeError:
            issues.append("LIVE_SOURCE_REGISTRY_PATH (authorized direct sources)")
    return issues


def _surface_issues(settings: RuntimeSettings, surface: str) -> list[str]:
    issues: list[str] = []
    if surface == "web":
        if settings.web_auth_mode != "supabase":
            issues.append("WEB_AUTH_MODE=supabase")
        if not settings.supabase_publishable_key:
            issues.append("SUPABASE_PUBLISHABLE_KEY")
        if not settings.web_allowed_origins:
            issues.append("WEB_ALLOWED_ORIGINS")
        for origin in settings.web_allowed_origins:
            if origin == "*" or not _is_https_url(origin):
                issues.append("WEB_ALLOWED_ORIGINS (explicit HTTPS origins only)")
                break
    elif surface == "streamlit":
        if settings.auth_mode != "google":
            issues.append("AUTH_MODE=google")
        if settings.access_policy not in {
            "google_any",
            "email_allowlist",
            "domain_allowlist",
        }:
            issues.append("ACCESS_POLICY")
        if (
            settings.access_policy == "email_allowlist"
            and not settings.allowed_emails
        ):
            issues.append("ALLOWED_EMAILS")
        if (
            settings.access_policy == "domain_allowlist"
            and not settings.allowed_domains
        ):
            issues.append("ALLOWED_DOMAINS")
        if not settings.admin_emails:
            issues.append("ADMIN_EMAILS")
    else:
        raise ValueError(f"Unknown hosted surface: {surface}")
    return issues


def validate_runtime(
    surface: str,
    *,
    settings: RuntimeSettings | None = None,
    check_database_revision: bool = True,
    revision_checker: RevisionChecker | None = None,
) -> RuntimeSettings:
    """Validate one hosted surface and return its immutable settings snapshot."""

    snapshot = settings or RuntimeSettings.from_env()
    if snapshot.app_env not in {"development", "test", "pilot", "production"}:
        raise RuntimeError(
            "APP_ENV must be one of development, test, pilot, or production"
        )
    if not snapshot.is_hosted:
        return snapshot

    issues = _common_issues(snapshot) + _surface_issues(snapshot, surface)
    if not issues and check_database_revision:
        checker = revision_checker or require_database_revision
        try:
            checker(snapshot.database_url)
        except RuntimeError as exc:
            issues.append(f"DATABASE_SCHEMA_REVISION ({exc})")
    if issues:
        raise RuntimeError(
            f"Unsafe {snapshot.app_env} {surface} configuration: "
            + ", ".join(issues)
        )
    return snapshot


def validate_web_runtime(**kwargs: object) -> RuntimeSettings:
    """Validate the hosted Next.js/FastAPI service configuration."""

    return validate_runtime("web", **kwargs)


def validate_streamlit_runtime(**kwargs: object) -> RuntimeSettings:
    """Validate the temporary hosted Streamlit compatibility surface."""

    return validate_runtime("streamlit", **kwargs)
