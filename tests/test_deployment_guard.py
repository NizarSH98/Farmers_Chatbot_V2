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
