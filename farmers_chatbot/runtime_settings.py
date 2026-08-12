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
    database_url: str
    auth_mode: str
    web_auth_mode: str
    access_policy: str
    allowed_emails: tuple[str, ...]
    allowed_domains: tuple[str, ...]
    admin_emails: tuple[str, ...]
    supabase_url: str
    supabase_publishable_key: str
    supabase_service_role_key: str
    supabase_storage_bucket: str
    web_allowed_origins: tuple[str, ...]
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
            database_url=get("DATABASE_URL"),
            auth_mode=get("AUTH_MODE", "disabled").lower(),
            web_auth_mode=get(
                "WEB_AUTH_MODE",
                "supabase" if app_env in HOSTED_ENVIRONMENTS else "disabled",
            ).lower(),
            access_policy=get("ACCESS_POLICY", "google_any").lower(),
            allowed_emails=_csv(get("ALLOWED_EMAILS"), lower=True),
            allowed_domains=_csv(get("ALLOWED_DOMAINS"), lower=True),
            admin_emails=_csv(get("ADMIN_EMAILS"), lower=True),
            supabase_url=get("SUPABASE_URL").rstrip("/"),
            supabase_publishable_key=get(
                "SUPABASE_PUBLISHABLE_KEY", get("SUPABASE_ANON_KEY")
            ),
            supabase_service_role_key=get("SUPABASE_SERVICE_ROLE_KEY"),
            supabase_storage_bucket=get("SUPABASE_STORAGE_BUCKET", "pilot-files"),
            web_allowed_origins=tuple(
                origin.rstrip("/") for origin in _csv(get("WEB_ALLOWED_ORIGINS"))
            ),
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
