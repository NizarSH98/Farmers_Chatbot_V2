"""Google OIDC identity and application authorization helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Mapping

from .config import (
    ACCESS_POLICY,
    ADMIN_EMAILS,
    ALLOWED_DOMAINS,
    ALLOWED_EMAILS,
    AUTH_MODE,
)

GOOGLE_ISSUERS = {'accounts.google.com', 'https://accounts.google.com'}


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


def identity_from_claims(claims: Mapping[str, Any]) -> UserIdentity:
    issuer = str(claims.get("iss") or "").strip()
    subject = str(claims.get("sub") or "").strip()
    email = str(claims.get("email") or "").strip().lower()
    name = str(claims.get("name") or email or "Pilot user").strip()
    email_verified = claims.get("email_verified")

    if issuer not in GOOGLE_ISSUERS:
        raise IdentityError('The identity was not issued by Google.')
    if not issuer or not subject:
        raise IdentityError("Google identity is missing issuer or subject.")
    if not email or email_verified not in {True, "true", "True", 1}:
        raise IdentityError("A verified Google email address is required.")
    if not access_allowed(email):
        raise IdentityError("This Google account is not allowed to access the pilot.")

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
    if ACCESS_POLICY == "google_any":
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


def current_streamlit_identity(st_module: Any) -> UserIdentity | None:
    """Return an authenticated identity, or None when login is required."""

    if AUTH_MODE == "disabled":
        return development_identity()
    if AUTH_MODE != "google":
        raise IdentityError("AUTH_MODE must be 'disabled' or 'google'.")

    user = st_module.user
    if not bool(getattr(user, "is_logged_in", False)):
        return None
    return identity_from_claims(dict(user))
