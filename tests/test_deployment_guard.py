import pytest

import farmers_chatbot.deployment_guard as guard


def test_development_runtime_allows_local_fallback(monkeypatch):
    monkeypatch.setattr(guard, "APP_ENV", "development")
    guard.validate_web_runtime()


def test_pilot_runtime_fails_closed_without_managed_services(monkeypatch):
    monkeypatch.setattr(guard, "APP_ENV", "pilot")
    monkeypatch.setattr(guard, "AUTH_MODE", "disabled")
    monkeypatch.setattr(guard, "DATABASE_URL", "")
    monkeypatch.setattr(guard, "SUPABASE_URL", "")
    monkeypatch.setattr(guard, "SUPABASE_SERVICE_ROLE_KEY", "")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="Unsafe pilot configuration"):
        guard.validate_web_runtime()


def test_pilot_runtime_accepts_complete_allowlisted_configuration(monkeypatch):
    monkeypatch.setattr(guard, "APP_ENV", "pilot")
    monkeypatch.setattr(guard, "APP_PUBLIC_URL", "https://pilot.streamlit.app")
    monkeypatch.setattr(guard, "AUTH_MODE", "google")
    monkeypatch.setattr(guard, "ACCESS_POLICY", "email_allowlist")
    monkeypatch.setattr(guard, "ALLOWED_EMAILS", frozenset({"tester@example.org"}))
    monkeypatch.setattr(guard, "ALLOWED_DOMAINS", frozenset())
    monkeypatch.setattr(guard, "ADMIN_EMAILS", frozenset({"admin@example.org"}))
    monkeypatch.setattr(guard, "DATABASE_URL", "postgresql://db.example/pilot")
    monkeypatch.setattr(guard, "SUPABASE_URL", "https://project.supabase.co")
    monkeypatch.setattr(guard, "SUPABASE_SERVICE_ROLE_KEY", "test-secret")
    monkeypatch.setattr(guard, "SUPABASE_STORAGE_BUCKET", "pilot-files")
    monkeypatch.setattr(guard, "ORGANIZATION_NAME", "Pilot operator")
    monkeypatch.setattr(guard, "PRIVACY_CONTACT_EMAIL", "privacy@example.org")
    monkeypatch.setattr(guard, "RETENTION_DAYS", 30)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    guard.validate_web_runtime()


def test_pilot_runtime_accepts_open_google_configuration(monkeypatch):
    monkeypatch.setattr(guard, "APP_ENV", "pilot")
    monkeypatch.setattr(guard, "APP_PUBLIC_URL", "https://raise.streamlit.app")
    monkeypatch.setattr(guard, "APP_DISPLAY_NAME", "RAISE")
    monkeypatch.setattr(guard, "AUTH_MODE", "google")
    monkeypatch.setattr(guard, "ACCESS_POLICY", "google_any")
    monkeypatch.setattr(guard, "ALLOWED_EMAILS", frozenset())
    monkeypatch.setattr(guard, "ALLOWED_DOMAINS", frozenset())
    monkeypatch.setattr(guard, "ADMIN_EMAILS", frozenset({"admin@example.org"}))
    monkeypatch.setattr(guard, "DATABASE_URL", "postgresql://db.example/project")
    monkeypatch.setattr(guard, "SUPABASE_URL", "https://project.supabase.co")
    monkeypatch.setattr(guard, "SUPABASE_SERVICE_ROLE_KEY", "test-secret")
    monkeypatch.setattr(guard, "SUPABASE_STORAGE_BUCKET", "pilot-files")
    monkeypatch.setattr(guard, "ORGANIZATION_NAME", "RAISE-ESDU")
    monkeypatch.setattr(guard, "PRIVACY_CONTACT_EMAIL", "privacy@example.org")
    monkeypatch.setattr(guard, "RETENTION_DAYS", 30)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    guard.validate_web_runtime()
