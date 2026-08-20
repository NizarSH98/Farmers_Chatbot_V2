import hashlib
import hmac
import importlib
import json
from types import SimpleNamespace

import pytest
from conftest import FakeReleaseKnowledge
from fastapi import FastAPI
from fastapi.testclient import TestClient

import farmers_chatbot.whatsapp_router as whatsapp_api
import whatsapp_api as compatibility_wrapper
from farmers_chatbot.assistant_contracts import TurnResult
from farmers_chatbot.pilot_store import PilotStore
from farmers_chatbot.storage_backends import LocalPrivateStorage
from farmers_chatbot.trusted_sources import TrustedSourceClient
from farmers_chatbot.turn_coordinator import TurnCoordinator


def _signed_body(payload: dict, secret: str) -> tuple[bytes, str]:
    body = json.dumps(payload, separators=(",", ":")).encode()
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return body, f"sha256={digest}"


def _services(tmp_path, pilot_store):
    return SimpleNamespace(
        knowledge=FakeReleaseKnowledge(),
        store=pilot_store,
        storage=LocalPrivateStorage(tmp_path / "private"),
        trusted=TrustedSourceClient(api_key=None, enabled=False),
        coordinator=TurnCoordinator(pilot_store),
        pipeline=SimpleNamespace(),
    )


def _client(services=None) -> TestClient:
    app = FastAPI()
    if services is not None:
        app.state.services = services
    app.include_router(whatsapp_api.router)
    return TestClient(app)


def test_root_module_is_only_a_canonical_app_wrapper():
    from farmers_chatbot.web_api import app as canonical_app

    refreshed = importlib.reload(compatibility_wrapper)
    assert refreshed.app is canonical_app


def test_whatsapp_is_fail_closed_until_explicitly_enabled(monkeypatch):
    monkeypatch.delenv("WHATSAPP_ENABLED", raising=False)
    with pytest.raises(
        RuntimeError,
        match="disabled until the canonical web soak passes",
    ):
        whatsapp_api._require_configuration()


def test_webhook_verification_signature_dedup_and_private_identity(
    monkeypatch,
    tmp_path,
):
    pilot_store = PilotStore(sqlite_path=tmp_path / "pilot.sqlite3")
    services = _services(tmp_path, pilot_store)
    monkeypatch.setattr(whatsapp_api, "META_APP_SECRET", "app-secret")
    monkeypatch.setattr(whatsapp_api, "META_VERIFY_TOKEN", "verify-token")
    monkeypatch.setattr(whatsapp_api, "META_ACCESS_TOKEN", "access-token")
    monkeypatch.setattr(whatsapp_api, "META_PHONE_NUMBER_ID", "phone-id")
    monkeypatch.setattr(whatsapp_api, "WHATSAPP_ID_SECRET", "identity-secret")
    monkeypatch.setenv('DATABASE_URL', 'postgresql://pilot:test@db.example/pilot')
    monkeypatch.setenv('OPENROUTER_API_KEY', 'test-key')
    monkeypatch.setenv("WHATSAPP_ENABLED", "true")
    sent = []
    monkeypatch.setattr(
        whatsapp_api,
        "_send_text",
        lambda recipient, body: sent.append((recipient, body)),
    )
    client = _client(services)

    verification = client.get(
        "/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "verify-token",
            "hub.challenge": "challenge-value",
        },
    )
    assert verification.status_code == 200
    assert verification.text == "challenge-value"

    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "metadata": {"phone_number_id": "phone-id"},
                            "messages": [
                                {
                                    "id": "wamid.test",
                                    "from": "96170123456",
                                    "type": "text",
                                    "text": {"body": "/help"},
                                }
                            ],
                        }
                    }
                ]
            }
        ],
    }
    body, signature = _signed_body(payload, "app-secret")
    response = client.post(
        "/webhooks/whatsapp",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": signature,
        },
    )
    assert response.status_code == 202
    assert response.json()["queued"] == 1
    assert sent and sent[0][0] == "96170123456"
    assert "Reply AGREE" in sent[0][1]
    with pilot_store._connect() as connection:
        assert connection.execute("SELECT COUNT(*) AS n FROM messages").fetchone()[
            "n"
        ] == 0

    duplicate = client.post(
        "/webhooks/whatsapp",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": signature,
        },
    )
    assert duplicate.status_code == 202
    assert duplicate.json()["duplicates"] == 1

    payload["entry"][0]["changes"][0]["value"]["messages"][0].update(
        {"id": "wamid.agree", "text": {"body": "AGREE"}}
    )
    agree_body, agree_signature = _signed_body(payload, "app-secret")
    agree = client.post(
        "/webhooks/whatsapp",
        content=agree_body,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": agree_signature,
        },
    )
    assert agree.status_code == 202

    payload["entry"][0]["changes"][0]["value"]["messages"][0].update(
        {"id": "wamid.help", "text": {"body": "/help"}}
    )
    help_body, help_signature = _signed_body(payload, "app-secret")
    help_response = client.post(
        "/webhooks/whatsapp",
        content=help_body,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": help_signature,
        },
    )
    assert help_response.status_code == 202

    with pilot_store._connect() as connection:
        users = connection.execute("SELECT subject, email FROM users").fetchall()
    assert len(users) == 1
    assert users[0]["subject"] != "96170123456"
    assert "96170123456" not in users[0]["subject"]
    assert not users[0]["email"]
    user = pilot_store.get_user(
        pilot_store.upsert_whatsapp_user(users[0]["subject"])["id"]
    )
    assert user["consent_at"]
    with pilot_store._connect() as connection:
        assert connection.execute("SELECT COUNT(*) AS n FROM messages").fetchone()[
            "n"
        ] == 1


def test_webhook_rejects_invalid_signature(monkeypatch):
    monkeypatch.setattr(whatsapp_api, "META_APP_SECRET", "app-secret")
    monkeypatch.setattr(whatsapp_api, "META_VERIFY_TOKEN", "verify-token")
    monkeypatch.setattr(whatsapp_api, "META_ACCESS_TOKEN", "access-token")
    monkeypatch.setattr(whatsapp_api, "META_PHONE_NUMBER_ID", "phone-id")
    monkeypatch.setattr(whatsapp_api, "WHATSAPP_ID_SECRET", "identity-secret")
    monkeypatch.setenv('DATABASE_URL', 'postgresql://pilot:test@db.example/pilot')
    monkeypatch.setenv('OPENROUTER_API_KEY', 'test-key')
    monkeypatch.setenv("WHATSAPP_ENABLED", "true")
    response = _client().post(
        "/webhooks/whatsapp",
        json={"object": "whatsapp_business_account", "entry": []},
        headers={"X-Hub-Signature-256": "sha256=bad"},
    )
    assert response.status_code == 401


def test_delivery_retry_reuses_persisted_turn_without_provider_rerun(
    monkeypatch,
    tmp_path,
):
    pilot_store = PilotStore(sqlite_path=tmp_path / "pilot.sqlite3")
    services = _services(tmp_path, pilot_store)
    monkeypatch.setattr(whatsapp_api, "META_APP_SECRET", "app-secret")
    monkeypatch.setattr(whatsapp_api, "META_VERIFY_TOKEN", "verify-token")
    monkeypatch.setattr(whatsapp_api, "META_ACCESS_TOKEN", "access-token")
    monkeypatch.setattr(whatsapp_api, "META_PHONE_NUMBER_ID", "phone-id")
    monkeypatch.setattr(whatsapp_api, "WHATSAPP_ID_SECRET", "identity-secret")
    monkeypatch.setenv("DATABASE_URL", "postgresql://pilot:test@db.example/pilot")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("WHATSAPP_ENABLED", "true")

    identity_hash = whatsapp_api.hash_external_identity(
        "96170123456",
        "identity-secret",
    )
    user = pilot_store.upsert_whatsapp_user(identity_hash)
    pilot_store.accept_consent(user["id"])
    provider_runs = 0

    async def fake_execute(
        services,
        command,
        *,
        history,
        tools,
        clarification_count,
    ):
        del services, history, tools, clarification_count
        nonlocal provider_runs
        provider_runs += 1
        return (
            TurnResult(
                content="Persisted agronomic answer.",
                kind="answer",
                language="en",
                model="test-model",
                citations=[
                    {
                        "title": "Test source",
                        "url": "https://example.test/source",
                    }
                ],
                provider_calls=[
                    {
                        "stage": "generation",
                        "model": "test-model",
                        "outcome": "success",
                        "duration_ms": 1,
                        "usage": {
                            "prompt_tokens": 5,
                            "completion_tokens": 3,
                            "cost_usd": 0.001,
                        },
                    }
                ],
            ),
            SimpleNamespace(
                analysis=SimpleNamespace(to_dict=lambda: {"intent": "advice"}),
                retrieval_metrics={"channels": ["lexical"]},
                graph_paths=[],
            ),
        )

    monkeypatch.setattr(whatsapp_api, "_execute_turn", fake_execute)
    deliveries = 0
    sent: list[tuple[str, str]] = []

    def flaky_send(recipient: str, body: str) -> None:
        nonlocal deliveries
        deliveries += 1
        if deliveries == 1:
            raise RuntimeError("temporary Meta delivery failure")
        sent.append((recipient, body))

    monkeypatch.setattr(whatsapp_api, "_send_text", flaky_send)
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "metadata": {"phone_number_id": "phone-id"},
                            "messages": [
                                {
                                    "id": "wamid.retry",
                                    "from": "96170123456",
                                    "type": "text",
                                    "text": {"body": "How should I improve my soil?"},
                                }
                            ],
                        }
                    }
                ]
            }
        ],
    }
    body, signature = _signed_body(payload, "app-secret")
    client = _client(services)

    first = client.post(
        "/webhooks/whatsapp",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": signature,
        },
    )
    assert first.status_code == 202
    assert pilot_store.get_whatsapp_event("wamid.retry")["status"] == "send_failed"
    assert provider_runs == 1

    retry = client.post(
        "/webhooks/whatsapp",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": signature,
        },
    )
    assert retry.status_code == 202
    assert retry.json() == {"status": "accepted", "queued": 1, "duplicates": 0}
    assert provider_runs == 1
    assert sent == [
        (
            "96170123456",
            (
                "Persisted agronomic answer.\n\n"
                "Sources:\nhttps://example.test/source"
            ),
        )
    ]
    assert pilot_store.get_whatsapp_event("wamid.retry")["status"] == "completed"
    with pilot_store._connect() as connection:
        assert connection.execute(
            "SELECT COUNT(*) AS n FROM assistant_turns"
        ).fetchone()["n"] == 1
        assert connection.execute(
            "SELECT COUNT(*) AS n FROM query_events"
        ).fetchone()["n"] == 1
        assert connection.execute(
            "SELECT COUNT(*) AS n FROM messages"
        ).fetchone()["n"] == 2
