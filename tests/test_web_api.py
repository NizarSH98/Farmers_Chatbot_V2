"""Tests for the authenticated FastAPI web API."""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import AsyncIterator

import httpx
import pytest
import pytest_asyncio

os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("DATABASE_URL", "")
os.environ.setdefault("OPENROUTER_API_KEY", "")
os.environ.setdefault("WEB_AUTH_MODE", "disabled")
os.environ.setdefault("WEB_ALLOWED_ORIGINS", "http://localhost:3000")

AUTH = {"Authorization": "Bearer test-token"}

pytestmark = pytest.mark.asyncio(loop_scope="function")


@pytest_asyncio.fixture()
async def client() -> AsyncIterator[httpx.AsyncClient]:
    with tempfile.TemporaryDirectory(prefix="raise_test_") as td:
        db_path = os.path.join(td, "web.sqlite3")
        os.environ["LOCAL_PILOT_DB_PATH"] = db_path

        import importlib

        import farmers_chatbot.config
        importlib.reload(farmers_chatbot.config)
        import farmers_chatbot.web_api as web_mod
        importlib.reload(web_mod)
        app = web_mod.app

        # Manually set up services (lifespan is not triggered by ASGITransport)
        from farmers_chatbot.assistant_pipeline import AsyncAssistantPipeline
        from farmers_chatbot.knowledge import KnowledgeIndex
        from farmers_chatbot.pilot_store import PilotStore
        from farmers_chatbot.storage_backends import LocalPrivateStorage
        from farmers_chatbot.supabase_auth import SupabaseAuthClient
        from farmers_chatbot.trusted_sources import TrustedSourceClient

        store = PilotStore(sqlite_path=db_path)
        storage = LocalPrivateStorage(root=os.path.join(td, "files"))
        knowledge = KnowledgeIndex.from_directory()
        trusted = TrustedSourceClient(None, enabled=False)
        auth = SupabaseAuthClient()
        test_http_client = httpx.AsyncClient()
        pipeline = AsyncAssistantPipeline(knowledge, client=test_http_client)

        app.state.services = web_mod.WebServices(
            store=store,
            storage=storage,
            knowledge=knowledge,
            trusted=trusted,
            auth=auth,
            pipeline=pipeline,
        )

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as ac:
            yield ac

        await pipeline.close()
        await auth.close()
        store.close()


async def test_healthz(client: httpx.AsyncClient) -> None:
    response = await client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def test_config(client: httpx.AsyncClient) -> None:
    response = await client.get("/v1/config")
    assert response.status_code == 200
    data = response.json()
    assert "modes" in data
    assert "models" in data
    assert data["default_language"] == "ar"


async def test_me_without_token_in_disabled_mode(client: httpx.AsyncClient) -> None:
    # In disabled auth mode, requests without tokens still return the local user
    response = await client.get("/v1/me")
    assert response.status_code == 200
    assert response.json()["email"] == "local@example.test"


async def test_me_with_auth(client: httpx.AsyncClient) -> None:
    response = await client.get("/v1/me", headers=AUTH)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "local@example.test"


async def test_usage_endpoint_returns_weekly_spend_and_limit(
    client: httpx.AsyncClient,
) -> None:
    from farmers_chatbot.config import MAX_USER_WEEKLY_COST_USD

    response = await client.get("/v1/usage", headers=AUTH)
    assert response.status_code == 200
    data = response.json()
    assert data["weekly_spend_usd"] == 0.0
    assert data["weekly_limit_usd"] == MAX_USER_WEEKLY_COST_USD
    assert "week_start" in data
    assert "week_end" in data


async def test_consent_flow(client: httpx.AsyncClient) -> None:
    response = await client.get("/v1/conversations", headers=AUTH)
    assert response.status_code == 428

    response = await client.post("/v1/consent", headers=AUTH)
    assert response.status_code == 204

    response = await client.get("/v1/conversations", headers=AUTH)
    assert response.status_code == 200


async def test_conversation_crud(client: httpx.AsyncClient) -> None:
    await client.post("/v1/consent", headers=AUTH)

    response = await client.post(
        "/v1/conversations",
        headers=AUTH,
        json={"title": "Test conversation"},
    )
    assert response.status_code == 201
    conversation = response.json()
    cid = conversation["id"]
    assert conversation["title"] == "Test conversation"

    response = await client.get("/v1/conversations", headers=AUTH)
    assert response.status_code == 200
    assert any(item["id"] == cid for item in response.json()["items"])

    response = await client.patch(
        f"/v1/conversations/{cid}",
        headers=AUTH,
        json={"title": "Renamed"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Renamed"

    response = await client.patch(
        f"/v1/conversations/{cid}",
        headers=AUTH,
        json={"archived": True},
    )
    assert response.status_code == 200

    response = await client.get("/v1/conversations", headers=AUTH)
    assert not any(item["id"] == cid for item in response.json()["items"])

    response = await client.delete(
        f"/v1/conversations/{cid}", headers=AUTH
    )
    assert response.status_code == 204


async def test_project_document_and_export_parity(
    client: httpx.AsyncClient,
) -> None:
    await client.post("/v1/consent", headers=AUTH)
    project = await client.post(
        "/v1/projects",
        headers=AUTH,
        json={"name": "Potato season", "instructions": "Prioritize Akkar."},
    )
    assert project.status_code == 201
    project_id = project.json()["id"]
    conversation = await client.post(
        "/v1/conversations",
        headers=AUTH,
        json={"title": "Project chat", "project_id": project_id},
    )
    assert conversation.status_code == 201
    assert conversation.json()["project_id"] == project_id

    uploaded = await client.post(
        f"/v1/projects/{project_id}/documents",
        headers=AUTH,
        files={
            "document": (
                "field-notes.txt",
                b"Akkar field observations\n\nIrrigation pressure is uneven.",
                "text/plain",
            )
        },
    )
    assert uploaded.status_code == 201
    document_id = uploaded.json()["id"]
    listed = await client.get(
        f"/v1/projects/{project_id}/documents", headers=AUTH
    )
    assert [item["id"] for item in listed.json()["items"]] == [document_id]
    download = await client.get(
        f"/v1/projects/{project_id}/documents/{document_id}/download",
        headers=AUTH,
    )
    assert download.status_code == 200
    assert download.content.startswith(b"Akkar field observations")

    exported = await client.get("/v1/export", headers=AUTH)
    assert exported.status_code == 200
    assert any(item["id"] == project_id for item in exported.json()["projects"])
    assert any(
        item["id"] == document_id for item in exported.json()["documents"]
    )

    deleted = await client.delete(
        f"/v1/projects/{project_id}/documents/{document_id}", headers=AUTH
    )
    assert deleted.status_code == 204
    missing = await client.get(
        f"/v1/projects/{project_id}/documents/{document_id}/download",
        headers=AUTH,
    )
    assert missing.status_code == 404


async def test_conversation_not_found(client: httpx.AsyncClient) -> None:
    await client.post("/v1/consent", headers=AUTH)
    response = await client.get(
        "/v1/conversations/nonexistent-id/messages",
        headers=AUTH,
    )
    assert response.status_code == 404


async def test_messages_empty(client: httpx.AsyncClient) -> None:
    await client.post("/v1/consent", headers=AUTH)
    response = await client.post(
        "/v1/conversations",
        headers=AUTH,
        json={"title": "Messages test"},
    )
    cid = response.json()["id"]

    response = await client.get(
        f"/v1/conversations/{cid}/messages", headers=AUTH
    )
    assert response.status_code == 200
    assert response.json()["items"] == []


async def test_sse_turn_stream(client: httpx.AsyncClient) -> None:
    """POST /v1/turns returns a valid SSE stream with user and assistant messages."""
    await client.post("/v1/consent", headers=AUTH)
    response = await client.post(
        "/v1/conversations",
        headers=AUTH,
        json={"title": "SSE test"},
    )
    cid = response.json()["id"]

    response = await client.post(
        "/v1/turns",
        headers={**AUTH, "X-Request-ID": "test-req-1"},
        json={
            "conversation_id": cid,
            "text": "What crops grow in Akkar?",
            "mode": "standard",
            "clarification_style": "auto",
            "attachment_ids": [],
        },
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    events = _parse_sse(response.text)
    event_types = [e["event"] for e in events]
    assert "turn.accepted" in event_types
    assert "status" in event_types
    assert event_types[-1] in {"turn.completed", "error"}

    response = await client.get(
        f"/v1/conversations/{cid}/messages", headers=AUTH
    )
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) >= 2
    roles = [item["role"] for item in items]
    assert "user" in roles
    assert "assistant" in roles


async def test_turn_idempotency_and_persisted_recovery(
    client: httpx.AsyncClient,
) -> None:
    await client.post("/v1/consent", headers=AUTH)
    created = await client.post(
        "/v1/conversations", headers=AUTH, json={"title": "Recovery"}
    )
    cid = created.json()["id"]
    turn_payload = {
        "conversation_id": cid,
        "text": "How can I improve irrigation efficiency?",
        "mode": "standard",
        "clarification_style": "auto",
        "attachment_ids": [],
    }
    headers = {
        **AUTH,
        "Idempotency-Key": "stable-turn-key",
        "X-Request-ID": "compatibility-alias-is-ignored",
    }
    first = await client.post("/v1/turns", headers=headers, json=turn_payload)
    assert first.status_code == 200
    first_events = _parse_sse(first.text)
    accepted = next(item for item in first_events if item["event"] == "turn.accepted")
    turn_id = accepted["data"]["turn_id"]
    assert accepted["data"]["request_id"] == "stable-turn-key"
    assert all("sequence" in item["data"] for item in first_events)

    status = await client.get(f"/v1/turns/{turn_id}", headers=AUTH)
    assert status.status_code == 200
    state = status.json()
    assert state["terminal"] is True
    assert state["request_id"] == "stable-turn-key"
    assert state["message"]["role"] == "assistant"

    replay = await client.post("/v1/turns", headers=headers, json=turn_payload)
    replay_events = _parse_sse(replay.text)
    assert replay_events[-1]["event"] == "turn.completed"
    assert replay_events[-1]["data"]["replayed"] is True
    assert replay_events[-1]["data"]["turn_id"] == turn_id

    messages = await client.get(
        f"/v1/conversations/{cid}/messages", headers=AUTH
    )
    assert len(messages.json()["items"]) == 2

    conflict = await client.post(
        "/v1/turns",
        headers=headers,
        json={**turn_payload, "text": "different payload"},
    )
    assert conflict.status_code == 409


async def test_turn_invalid_mode(client: httpx.AsyncClient) -> None:
    await client.post("/v1/consent", headers=AUTH)
    response = await client.post(
        "/v1/conversations",
        headers=AUTH,
        json={"title": "Invalid mode"},
    )
    cid = response.json()["id"]

    response = await client.post(
        "/v1/turns",
        headers=AUTH,
        json={
            "conversation_id": cid,
            "text": "test",
            "mode": "nonexistent_mode",
            "clarification_style": "auto",
            "attachment_ids": [],
        },
    )
    assert response.status_code == 422


async def test_feedback(client: httpx.AsyncClient) -> None:
    await client.post("/v1/consent", headers=AUTH)

    response = await client.post(
        "/v1/feedback",
        headers=AUTH,
        json={
            "category": "helpful",
            "comment": "Great agricultural advice!",
            "rating": 5,
            "language": "en",
        },
    )
    assert response.status_code == 201
    assert "id" in response.json()


async def test_image_upload_wrong_type(client: httpx.AsyncClient) -> None:
    await client.post("/v1/consent", headers=AUTH)

    response = await client.post(
        "/v1/uploads/images",
        headers=AUTH,
        files={"image": ("test.txt", b"not an image", "text/plain")},
    )
    assert response.status_code == 415


async def test_agreement_endpoint(client: httpx.AsyncClient) -> None:
    response = await client.get("/v1/legal/agreement?language=ar")
    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "ar"
    assert "markdown" in data

    response = await client.get("/v1/legal/agreement?language=en")
    assert response.status_code == 200
    assert response.json()["language"] == "en"


async def test_security_headers(client: httpx.AsyncClient) -> None:
    response = await client.get("/healthz")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert "max-age" in response.headers["strict-transport-security"]


async def test_delete_account(client: httpx.AsyncClient) -> None:
    await client.post("/v1/consent", headers=AUTH)
    response = await client.delete("/v1/account", headers=AUTH)
    assert response.status_code == 204


def _parse_sse(text: str) -> list[dict]:
    """Parse an SSE response body into a list of {event, data} dicts."""
    events: list[dict] = []
    current_event = ""
    current_data: list[str] = []
    for line in text.split("\n"):
        if line.startswith("event: "):
            current_event = line[7:]
        elif line.startswith("data: "):
            current_data.append(line[6:])
        elif line == "" and current_event:
            try:
                data = json.loads("\n".join(current_data))
            except json.JSONDecodeError:
                data = {}
            events.append({"event": current_event, "data": data})
            current_event = ""
            current_data = []
    return events
