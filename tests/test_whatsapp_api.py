import hashlib
import hmac
import json

from fastapi.testclient import TestClient

import whatsapp_api
from farmers_chatbot.knowledge import KnowledgeIndex
from farmers_chatbot.pilot_store import PilotStore
from farmers_chatbot.storage import EvidenceStore
from farmers_chatbot.trusted_sources import TrustedSourceClient


def _signed_body(payload: dict, secret: str) -> tuple[bytes, str]:
    body = json.dumps(payload, separators=(",", ":")).encode()
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return body, f"sha256={digest}"


def test_webhook_verification_signature_dedup_and_private_identity(
    monkeypatch,
    tmp_path,
):
    pilot_store = PilotStore(sqlite_path=tmp_path / "pilot.sqlite3")
    services = (
        KnowledgeIndex.from_directory(),
        pilot_store,
        EvidenceStore(tmp_path / "evidence.sqlite3"),
        TrustedSourceClient(api_key=None, enabled=False),
    )
    monkeypatch.setattr(whatsapp_api, "META_APP_SECRET", "app-secret")
    monkeypatch.setattr(whatsapp_api, "META_VERIFY_TOKEN", "verify-token")
    monkeypatch.setattr(whatsapp_api, "META_ACCESS_TOKEN", "access-token")
    monkeypatch.setattr(whatsapp_api, "META_PHONE_NUMBER_ID", "phone-id")
    monkeypatch.setattr(whatsapp_api, "WHATSAPP_ID_SECRET", "identity-secret")
    monkeypatch.setattr(whatsapp_api, "_services", lambda: services)
    monkeypatch.setenv('DATABASE_URL', 'postgresql://pilot:test@db.example/pilot')
    monkeypatch.setenv('OPENROUTER_API_KEY', 'test-key')
    sent = []
    monkeypatch.setattr(
        whatsapp_api,
        "_send_text",
        lambda recipient, body: sent.append((recipient, body)),
    )
    client = TestClient(whatsapp_api.app)

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
    response = TestClient(whatsapp_api.app).post(
        "/webhooks/whatsapp",
        json={"object": "whatsapp_business_account", "entry": []},
        headers={"X-Hub-Signature-256": "sha256=bad"},
    )
    assert response.status_code == 401
