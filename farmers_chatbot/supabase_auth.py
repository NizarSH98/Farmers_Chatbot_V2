"""Supabase Auth token validation and stable application identity linking."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from typing import Any

import httpx

from .config import (
    ADMIN_EMAILS,
    AUTH_CACHE_SECONDS,
    SUPABASE_PUBLISHABLE_KEY,
    SUPABASE_SERVICE_ROLE_KEY,
    SUPABASE_URL,
    WEB_AUTH_MODE,
)


class SupabaseAuthError(ValueError):
    """Raised when a browser access token is absent or cannot be verified."""


@dataclass(frozen=True)
class SupabaseIdentity:
    auth_user_id: str
    email: str
    name: str
    google_subject: str | None
    is_admin: bool


class SupabaseAuthClient:
    def __init__(
        self,
        *,
        url: str = SUPABASE_URL,
        publishable_key: str = SUPABASE_PUBLISHABLE_KEY,
        service_role_key: str = SUPABASE_SERVICE_ROLE_KEY,
        cache_seconds: int = AUTH_CACHE_SECONDS,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.url = url.rstrip("/")
        self.publishable_key = publishable_key
        self.service_role_key = service_role_key
        self.cache_seconds = max(0, min(int(cache_seconds), 300))
        self._client = client or httpx.AsyncClient(
            timeout=httpx.Timeout(12.0, connect=5.0),
            limits=httpx.Limits(max_connections=30, max_keepalive_connections=10),
        )
        self._owns_client = client is None
        self._cache: dict[str, tuple[float, SupabaseIdentity]] = {}

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def validate(self, access_token: str) -> SupabaseIdentity:
        if WEB_AUTH_MODE == "disabled":
            return SupabaseIdentity(
                auth_user_id="local-web-user",
                email="local@example.test",
                name="Local RAISE user",
                google_subject=None,
                is_admin=True,
            )
        if WEB_AUTH_MODE != "supabase":
            raise SupabaseAuthError("WEB_AUTH_MODE must be 'supabase' or 'disabled'")
        if not self.url or not self.publishable_key:
            raise SupabaseAuthError("Supabase Auth is not configured")
        token = access_token.strip()
        if not token:
            raise SupabaseAuthError("Authentication token is required")

        cache_key = hashlib.sha256(token.encode("utf-8")).hexdigest()
        cached = self._cache.get(cache_key)
        if cached and cached[0] > time.monotonic():
            return cached[1]

        response = await self._client.get(
            f"{self.url}/auth/v1/user",
            headers={
                "Authorization": f"Bearer {token}",
                "apikey": self.publishable_key,
            },
        )
        if response.status_code != 200:
            raise SupabaseAuthError("The session is invalid or expired")
        data = response.json()
        identity = self._identity_from_user(data)
        self._cache[cache_key] = (
            time.monotonic() + self.cache_seconds,
            identity,
        )
        if len(self._cache) > 500:
            now = time.monotonic()
            self._cache = {
                key: value for key, value in self._cache.items() if value[0] > now
            }
        return identity

    @staticmethod
    def _identity_from_user(data: dict[str, Any]) -> SupabaseIdentity:
        auth_user_id = str(data.get("id") or "").strip()
        email = str(data.get("email") or "").strip().lower()
        metadata = data.get("user_metadata") or {}
        confirmed = bool(
            data.get("email_confirmed_at")
            or metadata.get("email_verified") is True
        )
        if not auth_user_id or not email or not confirmed:
            raise SupabaseAuthError("A verified Google email address is required")

        google_subject = None
        for identity in data.get("identities") or []:
            if identity.get("provider") != "google":
                continue
            identity_data = identity.get("identity_data") or {}
            google_subject = str(
                identity.get("provider_id")
                or identity_data.get("sub")
                or ""
            ).strip() or None
            break
        if not google_subject:
            raise SupabaseAuthError("A verified Google identity is required")

        name = str(
            metadata.get("full_name")
            or metadata.get("name")
            or email.split("@", 1)[0]
        ).strip()
        return SupabaseIdentity(
            auth_user_id=auth_user_id,
            email=email,
            name=name[:200],
            google_subject=google_subject,
            is_admin=email in ADMIN_EMAILS,
        )

    async def delete_user(self, auth_user_id: str) -> None:
        if WEB_AUTH_MODE == "disabled":
            return
        if not self.url or not self.service_role_key:
            raise SupabaseAuthError("Supabase administrator access is not configured")
        response = await self._client.delete(
            f"{self.url}/auth/v1/admin/users/{auth_user_id}",
            headers={
                "Authorization": f"Bearer {self.service_role_key}",
                "apikey": self.service_role_key,
            },
        )
        if response.status_code not in {200, 204}:
            raise SupabaseAuthError("The authentication account could not be deleted")
