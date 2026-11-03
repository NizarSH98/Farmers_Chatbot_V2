"""Application-session behavior independent of any specific OIDC provider."""

from __future__ import annotations

import time
from types import SimpleNamespace

import pytest

from farmers_chatbot.oidc_auth import OidcAuthClient, OidcAuthError


def test_disabled_auth_returns_only_the_explicit_development_identity() -> None:
    client = OidcAuthClient(web_auth_mode="disabled")
    request = SimpleNamespace(session={})
    status = client.session_status(request)
    assert status["authenticated"] is True
    assert status["identity"]["issuer"] == "local-development"
    assert status["csrf_token"] == "local-development"


def test_expired_application_session_is_cleared() -> None:
    client = OidcAuthClient(
        web_auth_mode="oidc",
        issuer_url="https://identity.example.test",
        client_id="client",
        client_secret="secret",
        redirect_uri="https://app.example.test/api/auth/callback",
    )
    request = SimpleNamespace(
        session={
            "identity": {
                "issuer": "https://identity.example.test",
                "subject": "user-1",
                "email": "user@example.test",
                "name": "User",
                "is_admin": False,
                "expires_at": int(time.time()) - 1,
            },
            "csrf_token": "token",
        }
    )
    with pytest.raises(OidcAuthError, match="expired"):
        client.identity(request)
    assert request.session == {}


def test_valid_application_session_exposes_no_provider_token() -> None:
    client = OidcAuthClient(
        web_auth_mode="oidc",
        issuer_url="https://identity.example.test",
        client_id="client",
        client_secret="secret",
        redirect_uri="https://app.example.test/api/auth/callback",
    )
    request = SimpleNamespace(
        session={
            "identity": {
                "issuer": "https://identity.example.test",
                "subject": "user-1",
                "email": "user@example.test",
                "name": "User",
                "is_admin": False,
                "expires_at": int(time.time()) + 60,
            },
            "csrf_token": "csrf",
        }
    )
    status = client.session_status(request)
    assert status["authenticated"] is True
    assert status["csrf_token"] == "csrf"
    assert "access_token" not in str(status)
