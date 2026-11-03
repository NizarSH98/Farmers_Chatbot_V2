"""OIDC identity and application authorization helpers."""

from __future__ import annotations

import os
import time
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .config import (
    ACCESS_POLICY,
    ADMIN_EMAILS,
    ALLOWED_DOMAINS,
    ALLOWED_EMAILS,
    OIDC_ISSUER_URL,
)


@dataclass(frozen=True)
class UserIdentity:
    user_id: str
    issuer: str
    subject: str
    email: str
    name: str
    is_admin: bool
    is_development: bool = False


class IdentityError(ValueError):
    """Raised when an identity is missing required verified claims."""


def identity_from_claims(
    claims: Mapping[str, Any],
    *,
    expected_issuer: str | None = None,
) -> UserIdentity:
    issuer = str(claims.get("iss") or "").strip()
    subject = str(claims.get("sub") or "").strip()
    email = str(claims.get("email") or "").strip().lower()
    name = str(claims.get("name") or email or "Pilot user").strip()
    email_verified = claims.get("email_verified")
    expires_at = claims.get("exp")

    configured_issuer = (expected_issuer or OIDC_ISSUER_URL).rstrip("/")
    if configured_issuer and issuer.rstrip("/") != configured_issuer:
        raise IdentityError("The identity has an unexpected OIDC issuer.")
    if not issuer or not subject:
        raise IdentityError("OIDC identity is missing issuer or subject.")
    if not email or email_verified not in {True, "true", "True"}:
        raise IdentityError("A verified email address is required.")
    if expires_at is not None:
        try:
            expired = int(expires_at) <= int(time.time())
        except (TypeError, ValueError) as exc:
            raise IdentityError("OIDC identity has an invalid expiry claim.") from exc
        if expired:
            raise IdentityError("OIDC session expired. Log out and sign in again.")
    if not access_allowed(email):
        raise IdentityError("This account is not allowed to access the application.")

    return UserIdentity(
        user_id="",
        issuer=issuer,
        subject=subject,
        email=email,
        name=name[:200],
        is_admin=email in ADMIN_EMAILS,
    )


def access_allowed(email: str) -> bool:
    normalized = email.strip().lower()
    if ACCESS_POLICY == "any_verified_email":
        return True
    if ACCESS_POLICY == "email_allowlist":
        return normalized in ALLOWED_EMAILS
    if ACCESS_POLICY == "domain_allowlist":
        domain = normalized.rsplit("@", 1)[-1] if "@" in normalized else ""
        return domain in ALLOWED_DOMAINS
    return False


def development_identity() -> UserIdentity:
    subject = os.getenv("DEV_USER_ID", "local-pilot-user")
    email = os.getenv("DEV_USER_EMAIL", "local@example.test").lower()
    return UserIdentity(
        user_id="",
        issuer="local-development",
        subject=subject,
        email=email,
        name=os.getenv("DEV_USER_NAME", "Local pilot user"),
        is_admin=True,
        is_development=True,
    )
