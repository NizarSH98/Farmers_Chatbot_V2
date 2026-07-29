"""FastAPI webhook service for the Meta WhatsApp Cloud API pilot channel.

The webhook acknowledges accepted events immediately and completes model work in a
background task. Only an HMAC-derived user identifier and the message text are
persisted; the raw phone number exists in memory only long enough to send the reply.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import re
from functools import lru_cache
from typing import Any

import requests
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from farmers_chatbot.config import (
    META_ACCESS_TOKEN,
    META_APP_SECRET,
    META_GRAPH_API_VERSION,
    META_PHONE_NUMBER_ID,
    META_VERIFY_TOKEN,
    WHATSAPP_ID_SECRET,
    WHATSAPP_MAX_REPLY_CHARS,
)
from farmers_chatbot.knowledge import KnowledgeIndex
from farmers_chatbot.language import detect_language
from farmers_chatbot.llm import AssistantRequest, AssistantService
from farmers_chatbot.pilot_store import PilotStore, hash_external_identity
from farmers_chatbot.storage import EvidenceStore
from farmers_chatbot.tools import ToolRegistry
from farmers_chatbot.trusted_sources import TrustedSourceClient

app = FastAPI(
    title="RAISE ESDU WhatsApp Pilot",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
)


@lru_cache(maxsize=1)
def _services() -> tuple[
    KnowledgeIndex,
    PilotStore,
    EvidenceStore,
    TrustedSourceClient,
]:
    return (
        KnowledgeIndex.from_directory(),
        PilotStore(),
        EvidenceStore(),
        TrustedSourceClient(
            os.getenv("OPENROUTER_API_KEY"),
            enabled=os.getenv("ENABLE_TRUSTED_WEB_SEARCH", "false").lower() == "true",
        ),
    )


def _require_configuration() -> None:
    database_url = os.getenv("DATABASE_URL", "")
    required = {
        "DATABASE_URL": (
            database_url
            if database_url.startswith(("postgres://", "postgresql://"))
            else ""
        ),
        "OPENROUTER_API_KEY": os.getenv("OPENROUTER_API_KEY", ""),
        "META_APP_SECRET": META_APP_SECRET,
        "META_VERIFY_TOKEN": META_VERIFY_TOKEN,
        "META_ACCESS_TOKEN": META_ACCESS_TOKEN,
        "META_PHONE_NUMBER_ID": META_PHONE_NUMBER_ID,
        "WHATSAPP_ID_SECRET": WHATSAPP_ID_SECRET,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise RuntimeError("Missing WhatsApp configuration: " + ", ".join(missing))


def _signature_is_valid(body: bytes, signature: str | None) -> bool:
    if not META_APP_SECRET or not signature or not signature.startswith("sha256="):
        return False
    expected = hmac.new(
        META_APP_SECRET.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(signature[7:], expected)


def _split_reply(text: str, maximum: int = WHATSAPP_MAX_REPLY_CHARS) -> list[str]:
    cleaned = text.strip()
    if not cleaned:
        return ["No answer was generated. Please try again."]
    parts: list[str] = []
    while len(cleaned) > maximum:
        boundary = cleaned.rfind("\n", 0, maximum)
        if boundary < maximum // 2:
            boundary = cleaned.rfind(" ", 0, maximum)
        if boundary < maximum // 2:
            boundary = maximum
        parts.append(cleaned[:boundary].strip())
        cleaned = cleaned[boundary:].strip()
    if cleaned:
        parts.append(cleaned)
    return parts


def _citation_links(citations: list[dict[str, Any]]) -> list[str]:
    links: list[str] = []
    for citation in citations:
        direct_url = citation.get("url")
        if isinstance(direct_url, str) and direct_url.startswith("https://"):
            links.append(direct_url)
        for source in citation.get("sources") or []:
            url = source.get("url")
            if isinstance(url, str) and url.startswith("https://"):
                links.append(url)
    return list(dict.fromkeys(links))[:5]


def _send_text(recipient: str, body: str) -> None:
    endpoint = (
        f"https://graph.facebook.com/{META_GRAPH_API_VERSION}/"
        f"{META_PHONE_NUMBER_ID}/messages"
    )
    response = requests.post(
        endpoint,
        headers={
            "Authorization": f"Bearer {META_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        },
        json={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": True, "body": body},
        },
        timeout=20,
    )
    response.raise_for_status()


def _feedback_command(
    store: PilotStore,
    user_id: str,
    conversation_id: str,
    text: str,
) -> str:
    comment = re.sub(r"^/feedback\b", "", text, flags=re.IGNORECASE).strip()
    if not comment:
        return "Usage: /feedback followed by a short comment."
    messages = store.list_messages(user_id, conversation_id)
    message_id = next(
        (
            message["id"]
            for message in reversed(messages)
            if message["role"] == "assistant"
        ),
        None,
    )
    store.record_feedback(
        user_id=user_id,
        message_id=message_id,
        category="other",
        comment=comment,
        consent=True,
        language=detect_language(comment),
    )
    return "Thank you. Your pilot feedback was recorded."


def _mode_command(store: PilotStore, user_id: str, text: str) -> str:
    requested = re.sub(r"^/mode\b", "", text, flags=re.IGNORECASE).strip().lower()
    normalized = requested.replace("-", "_")
    if normalized not in {"quick", "standard", "deep", "source_only"}:
        return "Modes: /mode quick, /mode standard, /mode deep, /mode source-only"
    store.update_user_preferences(user_id, default_mode=normalized)
    return f"Default mode changed to {normalized.replace('_', '-')}."


def _handle_command(
    store: PilotStore,
    user_id: str,
    conversation_id: str,
    text: str,
) -> tuple[str | None, str]:
    command = text.strip().split(maxsplit=1)[0].lower()
    if command == "/help":
        return (
            (
                "Ask a farming, scientific, or rural-enterprise question naturally.\n"
                "Commands: /new, /help, /mode, /feedback.\n"
                "This is an internal pilot; verify urgent or high-risk advice with a "
                "qualified local professional."
            ),
            conversation_id,
        )
    if command == "/new":
        store.archive_conversation(user_id, conversation_id)
        new_conversation = store.create_conversation(
            user_id,
            "WhatsApp conversation",
            channel="whatsapp",
        )
        return "A new WhatsApp conversation has started.", new_conversation
    if command == "/mode":
        return _mode_command(store, user_id, text), conversation_id
    if command == "/feedback":
        return (
            _feedback_command(store, user_id, conversation_id, text),
            conversation_id,
        )
    return None, conversation_id


def _process_message(
    *,
    message_id: str,
    recipient: str,
    user_id: str,
    conversation_id: str,
    text: str,
) -> None:
    knowledge, store, evidence_store, trusted_client = _services()
    try:
        command_reply, conversation_id = _handle_command(
            store,
            user_id,
            conversation_id,
            text,
        )
        if command_reply:
            answer = command_reply
            response = None
        else:
            user = store.get_user(user_id)
            mode = str(user.get("default_mode") or "standard")
            rate = store.check_rate_limit(user_id, mode)
            if not rate.allowed:
                answer = rate.message or "The pilot quota has been reached."
                response = None
            else:
                messages = store.list_messages(user_id, conversation_id)
                history = [
                    {"role": item["role"], "content": item["content"]}
                    for item in messages[:-1][-12:]
                    if item["role"] in {"user", "assistant"}
                ]
                tools = ToolRegistry(
                    knowledge,
                    evidence_store,
                    trusted_client=trusted_client,
                )
                response = AssistantService(knowledge, tools).answer_request(
                    AssistantRequest(
                        user_id=user_id,
                        channel="whatsapp",
                        conversation_id=conversation_id,
                        project_id=None,
                        text=text,
                        mode=mode,
                        clarification_style="auto",
                    ),
                    conversation_history=history,
                )
                answer = response.answer
                links = _citation_links(response.citations)
                if links:
                    answer += "\n\nSources:\n" + "\n".join(links)
                store.add_message(
                    user_id,
                    conversation_id,
                    role="assistant",
                    content=response.answer,
                    language=response.language,
                    mode=response.mode,
                    model=response.model,
                    status=response.kind,
                    citations=response.citations,
                    tools=response.tool_names,
                    warning=response.warning,
                )
                store.complete_query(
                    user_id,
                    mode=response.mode,
                    language=response.language,
                    duration_ms=response.duration_ms,
                    success=response.success,
                    error_type=response.error_type,
                    trusted_searches=response.trusted_searches,
                )
        for part in _split_reply(answer):
            _send_text(recipient, part)
        store.complete_whatsapp_event(message_id, status="completed")
    except Exception as exc:  # noqa: BLE001 - background provider boundary
        store.complete_whatsapp_event(
            message_id,
            status="failed",
            error_type=type(exc).__name__,
        )


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    try:
        _require_configuration()
        configured = True
    except RuntimeError:
        configured = False
    return {"status": "ok", "whatsapp_configured": configured}


@app.get("/webhooks/whatsapp", response_class=PlainTextResponse)
def verify_whatsapp_webhook(
    mode: str = Query(alias="hub.mode"),
    verify_token: str = Query(alias="hub.verify_token"),
    challenge: str = Query(alias="hub.challenge"),
) -> str:
    if (
        not META_VERIFY_TOKEN
        or mode != "subscribe"
        or not hmac.compare_digest(verify_token, META_VERIFY_TOKEN)
    ):
        raise HTTPException(status_code=403, detail="Verification failed")
    return challenge


@app.post("/webhooks/whatsapp", status_code=202)
async def receive_whatsapp_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
) -> dict[str, Any]:
    _require_configuration()
    raw_body = await request.body()
    if not _signature_is_valid(
        raw_body,
        request.headers.get("X-Hub-Signature-256"),
    ):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    try:
        payload = await request.json()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON") from exc
    if payload.get("object") != "whatsapp_business_account":
        raise HTTPException(status_code=400, detail="Unexpected webhook object")

    _, store, _, _ = _services()
    accepted = 0
    duplicates = 0
    for entry in payload.get("entry") or []:
        for change in entry.get("changes") or []:
            value = change.get("value") or {}
            phone_number_id = str(
                (value.get("metadata") or {}).get("phone_number_id") or ""
            )
            if phone_number_id != META_PHONE_NUMBER_ID:
                raise HTTPException(status_code=400, detail="Phone number ID mismatch")
            for message in value.get("messages") or []:
                if message.get("type") != "text":
                    continue
                message_id = str(message.get("id") or "")
                sender = str(message.get("from") or "")
                text = str((message.get("text") or {}).get("body") or "").strip()
                if not message_id or not sender or not text:
                    continue
                identity_hash = hash_external_identity(sender, WHATSAPP_ID_SECRET)
                if not store.register_whatsapp_event(message_id, identity_hash):
                    duplicates += 1
                    continue
                user = store.upsert_whatsapp_user(identity_hash)
                conversation_id = store.get_or_create_channel_conversation(
                    user["id"],
                    "whatsapp",
                )
                store.add_message(
                    user["id"],
                    conversation_id,
                    role="user",
                    content=text,
                    language=detect_language(text),
                )
                background_tasks.add_task(
                    _process_message,
                    message_id=message_id,
                    recipient=sender,
                    user_id=user["id"],
                    conversation_id=conversation_id,
                    text=text,
                )
                accepted += 1
    return {"status": "accepted", "queued": accepted, "duplicates": duplicates}
