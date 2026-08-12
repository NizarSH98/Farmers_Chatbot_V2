"""Disabled-by-default WhatsApp router for the canonical FastAPI service."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import os
import re
import time
from typing import Any

import requests
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from .artifacts import ArtifactService
from .assistant_contracts import TurnCommand
from .config import (
    META_ACCESS_TOKEN,
    META_APP_SECRET,
    META_GRAPH_API_VERSION,
    META_PHONE_NUMBER_ID,
    META_VERIFY_TOKEN,
    WHATSAPP_ID_SECRET,
    WHATSAPP_MAX_REPLY_CHARS,
)
from .language import detect_language
from .legal import whatsapp_consent_message
from .pilot_store import hash_external_identity
from .tools import ToolRegistry

router = APIRouter(tags=["whatsapp"])


def _require_configuration() -> None:
    if os.getenv("WHATSAPP_ENABLED", "false").lower() != "true":
        raise RuntimeError("WhatsApp is disabled until the canonical web soak passes")
    required = {
        "META_APP_SECRET": META_APP_SECRET,
        "META_VERIFY_TOKEN": META_VERIFY_TOKEN,
        "META_ACCESS_TOKEN": META_ACCESS_TOKEN,
        "META_PHONE_NUMBER_ID": META_PHONE_NUMBER_ID,
        "WHATSAPP_ID_SECRET": WHATSAPP_ID_SECRET,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise RuntimeError("Missing WhatsApp configuration: " + ", ".join(missing))


def _services(request: Request) -> Any:
    services = getattr(request.app.state, "services", None)
    if services is None:
        raise HTTPException(status_code=503, detail="Service container unavailable")
    return services


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


def _answer_with_citations(
    content: str,
    citations: list[dict[str, Any]] | None,
) -> str:
    links = _citation_links(citations or [])
    return content if not links else content + "\n\nSources:\n" + "\n".join(links)


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


async def _send_answer(recipient: str, answer: str) -> None:
    for part in _split_reply(answer):
        await asyncio.to_thread(_send_text, recipient, part)


def _feedback_command(
    store: Any,
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


def _mode_command(store: Any, user_id: str, text: str) -> str:
    requested = re.sub(r"^/mode\b", "", text, flags=re.IGNORECASE).strip().lower()
    normalized = requested.replace("-", "_")
    if normalized not in {"quick", "standard", "deep", "source_only"}:
        return "Modes: /mode quick, /mode standard, /mode deep, /mode source-only"
    store.update_user_preferences(user_id, default_mode=normalized)
    return f"Default mode changed to {normalized.replace('_', '-')}."


def _handle_command(
    store: Any,
    user_id: str,
    conversation_id: str,
    text: str,
) -> tuple[str | None, str]:
    command = text.strip().split(maxsplit=1)[0].lower()
    if command == "/help":
        return (
            (
                "Ask a farming, scientific, or rural-enterprise question naturally.\n"
                "Commands: /new, /help, /mode, /feedback, /privacy, /delete.\n"
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
        return _feedback_command(store, user_id, conversation_id, text), conversation_id
    if command == "/privacy":
        return whatsapp_consent_message(), conversation_id
    if command == "/delete":
        if text.strip().lower() != "/delete confirm":
            return (
                (
                    "To permanently delete this WhatsApp pilot history and identity, "
                    "send: /delete confirm"
                ),
                conversation_id,
            )
        store.delete_user_records(user_id)
        return "Your WhatsApp pilot identity and history were deleted.", conversation_id
    return None, conversation_id


async def _retry_persisted_message(
    *,
    services: Any,
    message_id: str,
    recipient: str,
    user_id: str,
) -> None:
    store = services.store
    try:
        state = await asyncio.to_thread(
            store.get_assistant_turn_by_request_id,
            user_id,
            message_id,
        )
        message = state.get("message") if state else None
        if not state or not message or state.get("status") not in {
            "complete",
            "awaiting_clarification",
            "refused",
        }:
            await asyncio.to_thread(
                store.complete_whatsapp_event,
                message_id,
                status="failed",
                error_type="PersistedTurnUnavailable",
            )
            return
        answer = _answer_with_citations(
            str(message.get("content") or ""),
            message.get("citations") or [],
        )
        await _send_answer(recipient, answer)
        await asyncio.to_thread(
            store.complete_whatsapp_event,
            message_id,
            status="completed",
        )
    except Exception as exc:  # noqa: BLE001 - channel delivery boundary
        await asyncio.to_thread(
            store.complete_whatsapp_event,
            message_id,
            status="send_failed",
            error_type=type(exc).__name__,
        )


async def _execute_turn(
    services: Any,
    command: TurnCommand,
    *,
    history: list[dict[str, str]],
    tools: ToolRegistry,
    clarification_count: int,
) -> tuple[Any, Any]:
    prepared = await services.pipeline.prepare(
        command,
        tools=tools,
        history=history,
        clarification_count=clarification_count,
    )
    result = None
    async for event in services.pipeline.stream(
        command,
        prepared,
        tools=tools,
        history=history,
    ):
        if event.result is not None:
            result = event.result
    if result is None:
        raise RuntimeError("Assistant engine ended without a terminal result")
    return result, prepared


async def _process_message(
    *,
    services: Any,
    message_id: str,
    recipient: str,
    user_id: str,
    conversation_id: str,
    text: str,
) -> None:
    store = services.store
    turn_id: str | None = None
    owns_reservation = False
    generated_persisted = False
    started = time.perf_counter()
    try:
        if not await asyncio.to_thread(store.has_current_consent, user_id):
            if text.strip().lower() in {"agree", "/agree"}:
                await asyncio.to_thread(store.accept_consent, user_id)
                answer = (
                    "Thank you. Consent was recorded. Send your first question when "
                    "you are ready."
                )
            else:
                answer = whatsapp_consent_message()
            await _send_answer(recipient, answer)
            await asyncio.to_thread(
                store.complete_whatsapp_event,
                message_id,
                status="completed",
            )
            return
        command_name = text.strip().split(maxsplit=1)[0].lower()
        if command_name in {
            "/help",
            "/new",
            "/mode",
            "/feedback",
            "/privacy",
            "/delete",
        }:
            await asyncio.to_thread(
                store.add_message,
                user_id,
                conversation_id,
                role="user",
                content=text,
                language=detect_language(text),
            )
        command_reply, conversation_id = await asyncio.to_thread(
            _handle_command,
            store,
            user_id,
            conversation_id,
            text,
        )
        if command_reply:
            answer = command_reply
        else:
            user = await asyncio.to_thread(store.get_user, user_id)
            command = TurnCommand(
                request_id=message_id,
                actor_id=user_id,
                channel="whatsapp",
                conversation_id=conversation_id,
                text=text,
                mode=str(user.get("default_mode") or "standard"),
            )
            clarification_count = await asyncio.to_thread(
                store.consecutive_clarifications,
                user_id,
                conversation_id,
            )
            reservation = await asyncio.to_thread(
                services.coordinator.reserve,
                command,
                language=detect_language(text),
                stored_attachments=[],
                clarification_count=clarification_count,
            )
            turn_id = reservation.turn_id
            owns_reservation = bool(reservation.allowed and not reservation.existing)
            if not reservation.allowed:
                answer = reservation.message or "The pilot quota has been reached."
            elif reservation.existing:
                state = await asyncio.to_thread(
                    services.coordinator.status,
                    user_id,
                    str(reservation.turn_id),
                )
                message = state.get("message")
                if not state.get("terminal") or not message:
                    raise RuntimeError("Existing turn has no terminal result to deliver")
                answer = _answer_with_citations(
                    str(message.get("content") or ""),
                    message.get("citations") or [],
                )
                generated_persisted = True
            else:
                messages = await asyncio.to_thread(
                    store.list_messages,
                    user_id,
                    conversation_id,
                )
                history = [
                    {"role": item["role"], "content": item["content"]}
                    for item in messages[:-1][-12:]
                    if item["role"] in {"user", "assistant"}
                ]
                artifact_service = ArtifactService(
                    store,
                    services.storage,
                    owner_user_id=user_id,
                    conversation_id=conversation_id,
                )
                tools = ToolRegistry(
                    services.knowledge,
                    store,
                    trusted_client=services.trusted,
                    artifact_service=artifact_service,
                )
                result, prepared = await _execute_turn(
                    services,
                    command,
                    history=history,
                    tools=tools,
                    clarification_count=clarification_count,
                )
                result.duration_ms = int((time.perf_counter() - started) * 1000)
                await asyncio.to_thread(
                    services.coordinator.finalize,
                    command,
                    str(turn_id),
                    result,
                    analysis={
                        **prepared.analysis.to_dict(),
                        "retrieval": prepared.retrieval_metrics,
                        "graph_paths": prepared.graph_paths,
                    },
                    terminal_sequence=1,
                )
                generated_persisted = True
                answer = _answer_with_citations(result.content, result.citations)
        await _send_answer(recipient, answer)
        await asyncio.to_thread(
            store.complete_whatsapp_event,
            message_id,
            status="completed",
        )
    except Exception as exc:  # noqa: BLE001 - background provider/delivery boundary
        failure_type = type(exc).__name__
        if turn_id and owns_reservation and not generated_persisted:
            try:
                await asyncio.to_thread(
                    services.coordinator.fail,
                    user_id,
                    turn_id,
                    status="failed",
                    error_type=type(exc).__name__,
                    duration_ms=int((time.perf_counter() - started) * 1000),
                    terminal_sequence=1,
                )
            except Exception as finalize_exc:  # noqa: BLE001
                failure_type += f"+finalize_{type(finalize_exc).__name__}"
        await asyncio.to_thread(
            store.complete_whatsapp_event,
            message_id,
            status="send_failed" if generated_persisted else "failed",
            error_type=failure_type,
        )


@router.get("/webhooks/whatsapp/healthz")
def whatsapp_healthz() -> dict[str, Any]:
    try:
        _require_configuration()
        configured = True
    except RuntimeError:
        configured = False
    return {"status": "ok", "whatsapp_configured": configured}


@router.get("/webhooks/whatsapp", response_class=PlainTextResponse)
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


@router.post("/webhooks/whatsapp", status_code=202)
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

    services = _services(request)
    store = services.store
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
                registered = await asyncio.to_thread(
                    store.register_whatsapp_event,
                    message_id,
                    identity_hash,
                )
                if not registered:
                    event = await asyncio.to_thread(
                        store.get_whatsapp_event,
                        message_id,
                    )
                    if event and event.get("status") == "send_failed":
                        user = await asyncio.to_thread(
                            store.upsert_whatsapp_user,
                            identity_hash,
                        )
                        background_tasks.add_task(
                            _retry_persisted_message,
                            services=services,
                            message_id=message_id,
                            recipient=sender,
                            user_id=user["id"],
                        )
                        accepted += 1
                        continue
                    duplicates += 1
                    continue
                user = await asyncio.to_thread(
                    store.upsert_whatsapp_user,
                    identity_hash,
                )
                conversation_id = await asyncio.to_thread(
                    store.get_or_create_channel_conversation,
                    user["id"],
                    "whatsapp",
                )
                background_tasks.add_task(
                    _process_message,
                    services=services,
                    message_id=message_id,
                    recipient=sender,
                    user_id=user["id"],
                    conversation_id=conversation_id,
                    text=text,
                )
                accepted += 1
    return {"status": "accepted", "queued": accepted, "duplicates": duplicates}
