"""Versioned, side-effect-free settings for hosted service construction."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

from .config import AGREEMENT_TEXT_VERSION, MODEL_CATALOG

RUNTIME_SETTINGS_SCHEMA_VERSION = "raise-runtime-v1"
HOSTED_ENVIRONMENTS = frozenset({"pilot", "production"})


def _csv(values: str, *, lower: bool = False) -> tuple[str, ...]:
    parsed = tuple(value.strip() for value in values.split(",") if value.strip())
    if lower:
        return tuple(value.lower() for value in parsed)
    return parsed


def _boolean(value: str, default: bool = False) -> bool:
    normalized = value.strip().lower()
    if not normalized:
        return default
    return normalized in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class RuntimeSettings:
    """A stable snapshot of environment settings used during startup."""

    schema_version: str
    app_env: str
    app_public_url: str
    app_display_name: str
    organization_name: str
    privacy_contact_email: str
    consent_version: str
    agreement_text_version: str
    retention_days: int | None
    research_retention_days: int | None
    database_url: str
    qdrant_api_key: str
    web_auth_mode: str
    access_policy: str
    allowed_emails: tuple[str, ...]
    allowed_domains: tuple[str, ...]
    admin_emails: tuple[str, ...]
    oidc_issuer_url: str
    oidc_client_id: str
    oidc_client_secret: str
    oidc_scopes: str
    oidc_redirect_uri: str
    auth_post_login_redirect_url: str
    app_session_secret: str
    auth_session_max_age_seconds: int | None
    storage_backend: str
    local_file_root: str
    s3_endpoint_url: str
    s3_region: str
    s3_bucket: str
    s3_access_key_id: str
    s3_secret_access_key: str
    s3_force_path_style: bool
    openrouter_api_key: str
    openrouter_api_url: str
    openrouter_allowed_models: tuple[str, ...]
    openrouter_default_model: str
    openrouter_fast_model: str
    openrouter_deep_model: str
    request_analyzer_model: str
    answer_verifier_model: str
    trusted_search_enabled: bool
    live_source_registry_path: str
    openrouter_enforce_zdr: bool
    openrouter_data_collection: str

    @property
    def is_hosted(self) -> bool:
        return self.app_env in HOSTED_ENVIRONMENTS

    @classmethod
    def from_env(
        cls,
        environ: Mapping[str, str] | None = None,
    ) -> RuntimeSettings:
        """Capture environment values at startup rather than module import time."""

        values = os.environ if environ is None else environ

        def get(name: str, default: str = "") -> str:
            return values.get(name, default).strip()

        default_fast = get("OPENROUTER_FAST_MODEL", "moonshotai/kimi-k3")
        default_deep = get("OPENROUTER_DEEP_MODEL", "moonshotai/kimi-k3")
        configured_models = _csv(get("OPENROUTER_ALLOWED_MODELS"))
        allowed_models = configured_models or tuple(MODEL_CATALOG)
        retention_raw = get("RETENTION_DAYS", "30")
        try:
            retention_days: int | None = int(retention_raw)
        except ValueError:
            retention_days = None
        research_raw = get("RESEARCH_RETENTION_DAYS", "365")
        try:
            research_retention_days: int | None = int(research_raw)
        except ValueError:
            research_retention_days = None
        session_age_raw = get("AUTH_SESSION_MAX_AGE_SECONDS", "28800")
        try:
            session_age: int | None = int(session_age_raw)
        except ValueError:
            session_age = None

        app_env = get("APP_ENV", "development").lower()
        return cls(
            schema_version=RUNTIME_SETTINGS_SCHEMA_VERSION,
            app_env=app_env,
            app_public_url=get("APP_PUBLIC_URL").rstrip("/"),
            app_display_name=get("APP_DISPLAY_NAME", "RAISE"),
            organization_name=get("ORGANIZATION_NAME", "RAISE-ESDU"),
            privacy_contact_email=get(
                "PRIVACY_CONTACT_EMAIL",
                "privacy-contact-not-configured@example.invalid",
            ),
            consent_version=get("CONSENT_VERSION", AGREEMENT_TEXT_VERSION),
            agreement_text_version=AGREEMENT_TEXT_VERSION,
            retention_days=retention_days,
            research_retention_days=research_retention_days,
            database_url=get("DATABASE_URL"),
            qdrant_api_key=get("QDRANT_API_KEY"),
            web_auth_mode=get(
                "WEB_AUTH_MODE",
                "oidc" if app_env in HOSTED_ENVIRONMENTS else "disabled",
            ).lower(),
            access_policy=get("ACCESS_POLICY", "any_verified_email").lower(),
            allowed_emails=_csv(get("ALLOWED_EMAILS"), lower=True),
            allowed_domains=_csv(get("ALLOWED_DOMAINS"), lower=True),
            admin_emails=_csv(get("ADMIN_EMAILS"), lower=True),
            oidc_issuer_url=get("OIDC_ISSUER_URL").rstrip("/"),
            oidc_client_id=get("OIDC_CLIENT_ID"),
            oidc_client_secret=get("OIDC_CLIENT_SECRET"),
            oidc_scopes=get("OIDC_SCOPES", "openid email profile"),
            oidc_redirect_uri=get("OIDC_REDIRECT_URI"),
            auth_post_login_redirect_url=get(
                "AUTH_POST_LOGIN_REDIRECT_URL", get("APP_PUBLIC_URL")
            ).rstrip("/"),
            app_session_secret=get("APP_SESSION_SECRET"),
            auth_session_max_age_seconds=session_age,
            storage_backend=get("STORAGE_BACKEND", "local").lower(),
            local_file_root=get("LOCAL_FILE_ROOT", "data/pilot_files"),
            s3_endpoint_url=get("S3_ENDPOINT_URL").rstrip("/"),
            s3_region=get("S3_REGION", "us-east-1"),
            s3_bucket=get("S3_BUCKET"),
            s3_access_key_id=get("S3_ACCESS_KEY_ID"),
            s3_secret_access_key=get("S3_SECRET_ACCESS_KEY"),
            s3_force_path_style=_boolean(get("S3_FORCE_PATH_STYLE")),
            openrouter_api_key=get("OPENROUTER_API_KEY"),
            openrouter_api_url=get(
                "OPENROUTER_API_URL",
                "https://openrouter.ai/api/v1/chat/completions",
            ),
            openrouter_allowed_models=allowed_models,
            openrouter_default_model=get("OPENROUTER_DEFAULT_MODEL", default_fast),
            openrouter_fast_model=default_fast,
            openrouter_deep_model=default_deep,
            request_analyzer_model=get("REQUEST_ANALYZER_MODEL", default_fast),
            answer_verifier_model=get("ANSWER_VERIFIER_MODEL", default_fast),
            trusted_search_enabled=_boolean(
                get("ENABLE_TRUSTED_WEB_SEARCH"), default=False
            ),
            live_source_registry_path=get(
                "LIVE_SOURCE_REGISTRY_PATH",
                "config/live_sources.v1.json",
            ),
            openrouter_enforce_zdr=_boolean(
                get("OPENROUTER_ENFORCE_ZDR", "true"), default=True
            ),
            openrouter_data_collection=get(
                "OPENROUTER_DATA_COLLECTION", "deny"
            ).lower(),
        )
