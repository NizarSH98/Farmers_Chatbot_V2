from __future__ import annotations

import json
from collections.abc import Mapping

import pytest

from farmers_chatbot.deployment_guard import (
    validate_web_runtime,
)
from farmers_chatbot.migration_status import EXPECTED_DATABASE_REVISION
from farmers_chatbot.runtime_settings import RuntimeSettings


def _hosted_environment(**overrides: str) -> dict[str, str]:
    values = {
        "APP_ENV": "pilot",
        "APP_PUBLIC_URL": "https://raise.example.org",
        "APP_DISPLAY_NAME": "RAISE",
        "ORGANIZATION_NAME": "RAISE-ESDU",
        "PRIVACY_CONTACT_EMAIL": "privacy@example.org",
        "CONSENT_VERSION": "project-2026-11-v3",
        "RETENTION_DAYS": "30",
        "RESEARCH_RETENTION_DAYS": "365",
        "DATABASE_URL": "postgresql://user:secret@db.example.org/raise",
        "QDRANT_API_KEY": "a-strong-random-qdrant-key-over-32-characters",
        "STORAGE_BACKEND": "local",
        "LOCAL_FILE_ROOT": "/app/data/private",
        "WEB_AUTH_MODE": "oidc",
        "OIDC_ISSUER_URL": "https://identity.example.org",
        "OIDC_CLIENT_ID": "raise-web",
        "OIDC_CLIENT_SECRET": "oidc-client-secret",
        "OIDC_SCOPES": "openid email profile",
        "OIDC_REDIRECT_URI": "https://raise.example.org/api/auth/callback",
        "AUTH_POST_LOGIN_REDIRECT_URL": "https://raise.example.org",
        "APP_SESSION_SECRET": "a-long-random-session-secret-over-32-characters",
        "AUTH_SESSION_MAX_AGE_SECONDS": "28800",
        "ACCESS_POLICY": "any_verified_email",
        "ADMIN_EMAILS": "admin@example.org",
        "OPENROUTER_API_KEY": "openrouter-key",
        "OPENROUTER_ALLOWED_MODELS": "moonshotai/kimi-k3",
        "OPENROUTER_DEFAULT_MODEL": "moonshotai/kimi-k3",
        "OPENROUTER_FAST_MODEL": "moonshotai/kimi-k3",
        "OPENROUTER_DEEP_MODEL": "moonshotai/kimi-k3",
        "REQUEST_ANALYZER_MODEL": "moonshotai/kimi-k3",
        "ANSWER_VERIFIER_MODEL": "moonshotai/kimi-k3",
        "OPENROUTER_ENFORCE_ZDR": "true",
        "OPENROUTER_DATA_COLLECTION": "deny",
    }
    values.update(overrides)
    return values


def _settings(values: Mapping[str, str]) -> RuntimeSettings:
    return RuntimeSettings.from_env(values)


def test_development_runtime_allows_local_fallback() -> None:
    called = False

    def checker(_: str) -> str:
        nonlocal called
        called = True
        return "unexpected"

    settings = _settings({"APP_ENV": "development"})
    assert validate_web_runtime(settings=settings, revision_checker=checker) is settings
    assert not called


def test_unknown_environment_does_not_bypass_hosted_validation() -> None:
    with pytest.raises(RuntimeError, match="APP_ENV must be one of"):
        validate_web_runtime(settings=_settings({"APP_ENV": "prod"}))


def test_pilot_runtime_fails_closed_without_managed_services() -> None:
    with pytest.raises(RuntimeError, match="Unsafe pilot web configuration"):
        validate_web_runtime(
            settings=_settings({"APP_ENV": "pilot"}),
            check_database_revision=False,
        )


@pytest.mark.parametrize("environment", ["pilot", "production"])
def test_hosted_web_accepts_complete_configuration_at_expected_revision(
    environment: str,
) -> None:
    settings = _settings(_hosted_environment(APP_ENV=environment))
    result = validate_web_runtime(
        settings=settings,
        revision_checker=lambda _: "20260811_0001",
    )
    assert result is settings


def test_hosted_web_rejects_insecure_oidc_redirects() -> None:
    settings = _settings(
        _hosted_environment(
            OIDC_REDIRECT_URI="http://localhost:3000/api/auth/callback",
        )
    )
    with pytest.raises(RuntimeError, match="OIDC_REDIRECT_URI"):
        validate_web_runtime(settings=settings, check_database_revision=False)


def test_hosted_web_rejects_missing_qdrant_secret() -> None:
    settings = _settings(_hosted_environment(QDRANT_API_KEY=""))
    with pytest.raises(RuntimeError, match="QDRANT_API_KEY"):
        validate_web_runtime(settings=settings, check_database_revision=False)


@pytest.mark.parametrize("research_days", ["7", "731", "not-a-number"])
def test_hosted_web_rejects_out_of_range_research_retention(research_days) -> None:
    settings = _settings(
        _hosted_environment(RESEARCH_RETENTION_DAYS=research_days)
    )
    with pytest.raises(RuntimeError, match="RESEARCH_RETENTION_DAYS"):
        validate_web_runtime(settings=settings, check_database_revision=False)


def test_hosted_web_rejects_stale_consent_version() -> None:
    settings = _settings(_hosted_environment(CONSENT_VERSION="project-2026-09-v2"))
    with pytest.raises(RuntimeError, match="CONSENT_VERSION"):
        validate_web_runtime(settings=settings, check_database_revision=False)


def test_hosted_web_rejects_unapproved_stage_models() -> None:
    settings = _settings(
        _hosted_environment(ANSWER_VERIFIER_MODEL="provider/unapproved")
    )
    with pytest.raises(RuntimeError, match="ANSWER_VERIFIER_MODEL"):
        validate_web_runtime(settings=settings, check_database_revision=False)


def test_hosted_live_search_requires_an_authorized_direct_registry(tmp_path) -> None:
    empty = tmp_path / "empty-live.json"
    empty.write_text(
        json.dumps(
            {"schema_version": "raise-live-sources-v1", "sources": []}
        ),
        encoding="utf-8",
    )
    settings = _settings(
        _hosted_environment(
            ENABLE_TRUSTED_WEB_SEARCH="true",
            LIVE_SOURCE_REGISTRY_PATH=str(empty),
        )
    )
    with pytest.raises(RuntimeError, match="authorized direct sources"):
        validate_web_runtime(settings=settings, check_database_revision=False)

    authorized = tmp_path / "authorized-live.json"
    authorized.write_text(
        json.dumps(
            {
                "schema_version": "raise-live-sources-v1",
                "sources": [
                    {
                        "source_id": "FAO-DIRECT",
                        "publisher": "FAO",
                        "title": "FAO direct bulletin",
                        "url": "https://www.fao.org/direct-bulletin",
                        "categories": ["science"],
                        "ttl_seconds": 3600,
                        "authorized": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    ready = _settings(
        _hosted_environment(
            ENABLE_TRUSTED_WEB_SEARCH="true",
            LIVE_SOURCE_REGISTRY_PATH=str(authorized),
        )
    )
    assert (
        validate_web_runtime(
            settings=ready,
            revision_checker=lambda _: EXPECTED_DATABASE_REVISION,
        )
        is ready
    )


def test_hosted_web_fails_when_database_revision_is_not_ready() -> None:
    settings = _settings(_hosted_environment())

    def checker(_: str) -> str:
        raise RuntimeError("database revision is 'old'; expected 'head'")

    with pytest.raises(RuntimeError, match="DATABASE_SCHEMA_REVISION"):
        validate_web_runtime(settings=settings, revision_checker=checker)
