"""Standards-based OIDC login and signed application-session handling."""

from __future__ import annotations

import secrets
import time
from dataclasses import asdict
from typing import Any

from authlib.integrations.base_client import OAuthError
from authlib.integrations.starlette_client import OAuth
from starlette.requests import Request
from starlette.responses import RedirectResponse

from .auth import (
    IdentityError,
    UserIdentity,
    development_identity,
    identity_from_claims,
)
from .config import (
    AUTH_SESSION_MAX_AGE_SECONDS,
    OIDC_CLIENT_ID,
    OIDC_CLIENT_SECRET,
    OIDC_ISSUER_URL,
    OIDC_REDIRECT_URI,
    OIDC_SCOPES,
    WEB_AUTH_MODE,
)


class OidcAuthError(ValueError):
    """Raised when login state or an authenticated session is invalid."""


class OidcAuthClient:
    """OIDC authorization-code client with PKCE and signed local sessions."""

    def __init__(
        self,
        *,
        web_auth_mode: str = WEB_AUTH_MODE,
        issuer_url: str = OIDC_ISSUER_URL,
        client_id: str = OIDC_CLIENT_ID,
        client_secret: str = OIDC_CLIENT_SECRET,
        scopes: str = OIDC_SCOPES,
        redirect_uri: str = OIDC_REDIRECT_URI,
        session_max_age_seconds: int = AUTH_SESSION_MAX_AGE_SECONDS,
    ) -> None:
        self.web_auth_mode = web_auth_mode
        self.issuer_url = issuer_url.rstrip("/")
        self.redirect_uri = redirect_uri
        self.session_max_age_seconds = session_max_age_seconds
        self.oauth: OAuth | None = None
        if web_auth_mode == "oidc":
            self.oauth = OAuth()
            self.oauth.register(
                name="identity",
                server_metadata_url=(
                    f"{self.issuer_url}/.well-known/openid-configuration"
                ),
                client_id=client_id,
                client_secret=client_secret,
                client_kwargs={
                    "scope": scopes,
                    "code_challenge_method": "S256",
                },
            )
        elif web_auth_mode != "disabled":
            raise OidcAuthError("WEB_AUTH_MODE must be 'oidc' or 'disabled'")

    def _client(self) -> Any:
        if self.oauth is None:
            raise OidcAuthError("OIDC authentication is disabled")
        client = self.oauth.create_client("identity")
        if client is None:
            raise OidcAuthError("OIDC client configuration is unavailable")
        return client

    async def login(self, request: Request) -> RedirectResponse:
        if self.web_auth_mode == "disabled":
            raise OidcAuthError("OIDC authentication is disabled")
        return await self._client().authorize_redirect(
            request,
            self.redirect_uri,
        )

    async def callback(self, request: Request) -> UserIdentity:
        if self.web_auth_mode == "disabled":
            return development_identity()
        try:
            token = await self._client().authorize_access_token(request)
            claims = dict(token.get("userinfo") or {})
            if not claims:
                claims = dict(await self._client().userinfo(token=token))
        except OAuthError as exc:
            raise OidcAuthError("OIDC login could not be verified") from exc
        claims.setdefault("iss", self.issuer_url)
        try:
            identity = identity_from_claims(
                claims,
                expected_issuer=self.issuer_url,
            )
        except IdentityError as exc:
            raise OidcAuthError(str(exc)) from exc

        # Authlib's short-lived state/nonce/PKCE values are discarded here.
        # Only non-secret identity claims and a CSRF token remain in the signed,
        # HttpOnly session cookie; provider access/refresh tokens are never stored.
        request.session.clear()
        request.session["identity"] = {
            "issuer": identity.issuer,
            "subject": identity.subject,
            "email": identity.email,
            "name": identity.name,
            "is_admin": identity.is_admin,
            "expires_at": int(time.time()) + self.session_max_age_seconds,
        }
        request.session["csrf_token"] = secrets.token_urlsafe(32)
        return identity

    def identity(self, request: Request) -> UserIdentity:
        if self.web_auth_mode == "disabled":
            return development_identity()
        record = request.session.get("identity")
        if not isinstance(record, dict):
            raise OidcAuthError("Authentication is required")
        try:
            expires_at = int(record.get("expires_at") or 0)
        except (TypeError, ValueError) as exc:
            raise OidcAuthError("The application session is invalid") from exc
        if expires_at <= int(time.time()):
            request.session.clear()
            raise OidcAuthError("The application session expired")
        try:
            return UserIdentity(
                user_id="",
                issuer=str(record["issuer"]),
                subject=str(record["subject"]),
                email=str(record["email"]),
                name=str(record["name"]),
                is_admin=bool(record["is_admin"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise OidcAuthError("The application session is invalid") from exc

    def session_status(self, request: Request) -> dict[str, Any]:
        try:
            identity = self.identity(request)
        except OidcAuthError:
            return {"authenticated": False, "csrf_token": ""}
        public_identity = asdict(identity)
        public_identity.pop("user_id", None)
        public_identity.pop("is_development", None)
        return {
            "authenticated": True,
            "identity": public_identity,
            "csrf_token": (
                "local-development"
                if self.web_auth_mode == "disabled"
                else str(request.session.get("csrf_token") or "")
            ),
        }

    async def close(self) -> None:
        """Keep a uniform service lifecycle; Authlib owns per-request clients."""

