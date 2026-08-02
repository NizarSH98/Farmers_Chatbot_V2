"""Authenticated FastAPI surface for the RAISE web workspace."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import io
import json
import os
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

from fastapi import (
    Depends,
    FastAPI,
    File,
    Header,
    HTTPException,
    Query,
    Request,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from PIL import Image, ImageOps, UnidentifiedImageError
from pydantic import BaseModel, Field

from .artifacts import ArtifactService
from .assistant_pipeline import AsyncAssistantPipeline
from .config import (
    APP_DISPLAY_NAME,
    APP_ENV,
    CONSENT_VERSION,
    DATABASE_URL,
    MAX_CHAT_IMAGE_BYTES,
    MODE_PROFILES,
    MODEL_CATALOG,
    OPENROUTER_ALLOWED_MODELS,
    RETENTION_DAYS,
    WEB_ALLOWED_ORIGINS,
    WEB_AUTH_MODE,
)
from .knowledge import KnowledgeIndex
from .language import detect_language
from .legal import agreement_markdown, agreement_markdown_ar
from .llm import AssistantRequest
from .pilot_store import PilotStore
from .retention import purge_expired_content
from .storage_backends import PrivateFileStorage, configured_file_storage
from .supabase_auth import (
    SupabaseAuthClient,
    SupabaseAuthError,
    SupabaseIdentity,
)
from .tools import ToolRegistry
from .trusted_sources import TrustedSourceClient


@dataclass
class WebServices:
    store: PilotStore
    storage: PrivateFileStorage
    knowledge: KnowledgeIndex
    trusted: TrustedSourceClient
    auth: SupabaseAuthClient
    pipeline: AsyncAssistantPipeline


@dataclass(frozen=True)
class CurrentUser:
    record: dict[str, Any]
    identity: SupabaseIdentity

    @property
    def id(self) -> str:
        return str(self.record["id"])


class ConversationCreate(BaseModel):
    title: str = Field(default="New conversation", max_length=120)


class ConversationUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=120)
    archived: bool | None = None


class TurnRequest(BaseModel):
    conversation_id: str
    text: str = Field(min_length=1, max_length=8000)
    mode: str = "standard"
    model_id: str | None = None
    clarification_style: str = "auto"
    attachment_ids: list[str] = Field(default_factory=list, max_length=1)


class FeedbackRequest(BaseModel):
    category: str
    comment: str = Field(min_length=1, max_length=2000)
    rating: int | None = Field(default=None, ge=1, le=5)
    message_id: str | None = None
    language: str | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    if APP_ENV in {"pilot", "production"}:
        missing = []
        if not DATABASE_URL:
            missing.append("DATABASE_URL")
        if WEB_AUTH_MODE != "supabase":
            missing.append("WEB_AUTH_MODE=supabase")
        if missing:
            raise RuntimeError(
                "Web API production configuration is incomplete: "
                + ", ".join(missing)
            )
    store = PilotStore(
        database_url=os.getenv("DATABASE_URL", ""),
        sqlite_path=os.getenv("LOCAL_PILOT_DB_PATH", "data/pilot.sqlite3"),
    )
    storage = configured_file_storage()
    knowledge = KnowledgeIndex.from_directory()
    trusted = TrustedSourceClient(
        os.getenv("OPENROUTER_API_KEY"),
        enabled=os.getenv("ENABLE_TRUSTED_WEB_SEARCH", "false").lower() == "true",
    )
    auth = SupabaseAuthClient()
    pipeline = AsyncAssistantPipeline(knowledge)
    services = WebServices(store, storage, knowledge, trusted, auth, pipeline)
    app.state.services = services
    await asyncio.to_thread(purge_expired_content, store, RETENTION_DAYS, storage)
    try:
        yield
    finally:
        await pipeline.close()
        await auth.close()
        store.close()


app = FastAPI(
    title="RAISE Web API",
    version="2026.08",
    docs_url=None if APP_ENV in {"pilot", "production"} else "/docs",
    redoc_url=None,
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(WEB_ALLOWED_ORIGINS),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next: Any) -> Any:
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Server-Timing"] = (
        f"api;dur={(time.perf_counter() - started) * 1000:.1f}"
    )
    return response


def _services(request: Request) -> WebServices:
    return request.app.state.services


async def current_user(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> CurrentUser:
    token = ""
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
    services = _services(request)
    try:
        identity = await services.auth.validate(token)
        record = await asyncio.to_thread(
            services.store.upsert_supabase_user,
            auth_user_id=identity.auth_user_id,
            email=identity.email,
            name=identity.name,
            google_subject=identity.google_subject,
            is_admin=identity.is_admin,
        )
    except SupabaseAuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return CurrentUser(record=record, identity=identity)


def _require_consent(services: WebServices, user: CurrentUser) -> None:
    if not services.store.has_current_consent(user.id):
        raise HTTPException(status_code=428, detail="User agreement acceptance required")


def _sse(event: str, data: dict[str, Any]) -> bytes:
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return f"event: {event}\ndata: {payload}\n\n".encode()


def _delete_paths(storage: PrivateFileStorage, paths: list[str]) -> None:
    for path in dict.fromkeys(paths):
        storage.delete(path)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok", "service": "raise-web-api"}


@app.get("/v1/config")
async def public_config() -> dict[str, Any]:
    return {
        "app_name": APP_DISPLAY_NAME,
        "agreement_version": CONSENT_VERSION,
        "default_language": "ar",
        "modes": [
            {
                "id": key,
                "label_en": profile.label_en,
                "label_ar": profile.label_ar,
                "description": profile.description,
            }
            for key, profile in MODE_PROFILES.items()
        ],
        "models": [
            {
                "id": model.id,
                "label": model.label,
                "description": model.description,
                "supports_images": model.supports_images,
            }
            for model_id, model in MODEL_CATALOG.items()
            if model_id in OPENROUTER_ALLOWED_MODELS
        ],
    }


@app.get("/v1/me")
async def me(
    request: Request,
    user: Annotated[CurrentUser, Depends(current_user)],
) -> dict[str, Any]:
    services = _services(request)
    return {
        "id": user.id,
        "name": user.record["name"],
        "email": user.record.get("email"),
        "role": user.record["role"],
        "consent_current": await asyncio.to_thread(
            services.store.has_current_consent, user.id
        ),
        "default_mode": user.record.get("default_mode", "standard"),
    }


@app.get("/v1/legal/agreement")
async def agreement(
    language: str = Query(default="ar", pattern="^(ar|en)$"),
) -> dict[str, str]:
    return {
        "version": CONSENT_VERSION,
        "language": language,
        "markdown": (
            agreement_markdown_ar() if language == "ar" else agreement_markdown()
        ),
    }


@app.post("/v1/consent", status_code=204)
async def accept_consent(
    request: Request,
    user: Annotated[CurrentUser, Depends(current_user)],
) -> None:
    await asyncio.to_thread(_services(request).store.accept_consent, user.id)


@app.get("/v1/conversations")
async def list_conversations(
    request: Request,
    user: Annotated[CurrentUser, Depends(current_user)],
    search: str = Query(default="", max_length=120),
    include_archived: bool = False,
) -> dict[str, Any]:
    services = _services(request)
    _require_consent(services, user)
    items = await asyncio.to_thread(
        services.store.list_conversations,
        user.id,
        search=search,
        include_archived=include_archived,
    )
    return {"items": items}


@app.post("/v1/conversations", status_code=201)
async def create_conversation(
    payload: ConversationCreate,
    request: Request,
    user: Annotated[CurrentUser, Depends(current_user)],
) -> dict[str, Any]:
    services = _services(request)
    _require_consent(services, user)
    conversation_id = await asyncio.to_thread(
        services.store.create_conversation,
        user.id,
        payload.title,
        channel="web",
    )
    return await asyncio.to_thread(
        services.store.get_conversation, user.id, conversation_id
    )


@app.patch("/v1/conversations/{conversation_id}")
async def update_conversation(
    conversation_id: str,
    payload: ConversationUpdate,
    request: Request,
    user: Annotated[CurrentUser, Depends(current_user)],
) -> dict[str, Any]:
    services = _services(request)
    _require_consent(services, user)
    try:
        if payload.title is not None:
            await asyncio.to_thread(
                services.store.rename_conversation,
                user.id,
                conversation_id,
                payload.title,
            )
        if payload.archived is not None:
            await asyncio.to_thread(
                services.store.set_conversation_archived,
                user.id,
                conversation_id,
                payload.archived,
            )
        return await asyncio.to_thread(
            services.store.get_conversation, user.id, conversation_id
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.delete("/v1/conversations/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: str,
    request: Request,
    user: Annotated[CurrentUser, Depends(current_user)],
) -> None:
    services = _services(request)
    _require_consent(services, user)
    try:
        paths = await asyncio.to_thread(
            services.store.delete_conversation, user.id, conversation_id
        )
        await asyncio.to_thread(_delete_paths, services.storage, paths)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/v1/conversations/{conversation_id}/messages")
async def list_messages(
    conversation_id: str,
    request: Request,
    user: Annotated[CurrentUser, Depends(current_user)],
    limit: int = Query(default=60, ge=1, le=200),
    before: str | None = Query(default=None, max_length=80),
) -> dict[str, Any]:
    services = _services(request)
    _require_consent(services, user)
    try:
        items = await asyncio.to_thread(
            services.store.list_messages,
            user.id,
            conversation_id,
            limit=limit,
            before=before,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "items": items,
        "next_before": items[0]["created_at"] if len(items) == limit else None,
    }


@app.post("/v1/uploads/images", status_code=201)
async def upload_image(
    request: Request,
    user: Annotated[CurrentUser, Depends(current_user)],
    image: Annotated[UploadFile, File()],
) -> dict[str, Any]:
    services = _services(request)
    _require_consent(services, user)
    supplied_mime = (image.content_type or "").split(";", 1)[0].lower()
    if supplied_mime not in {"image/jpeg", "image/png"}:
        raise HTTPException(status_code=415, detail="Only JPG and PNG are accepted")
    data = await image.read(MAX_CHAT_IMAGE_BYTES + 1)
    if not data or len(data) > MAX_CHAT_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image must be under 5 MB")
    try:
        with Image.open(io.BytesIO(data)) as opened:
            opened.load()
            if opened.width > 12000 or opened.height > 12000:
                raise ValueError("Image dimensions are too large")
            cleaned = ImageOps.exif_transpose(opened)
            output = io.BytesIO()
            has_alpha = cleaned.mode in {"RGBA", "LA"} or (
                cleaned.mode == "P" and "transparency" in cleaned.info
            )
            if supplied_mime == "image/png" and has_alpha:
                cleaned.convert("RGBA").save(
                    output, format="PNG", optimize=True
                )
                stored_mime = "image/png"
                extension = "png"
            else:
                cleaned.convert("RGB").save(
                    output, format="JPEG", quality=88, optimize=True
                )
                stored_mime = "image/jpeg"
                extension = "jpg"
            sanitized = output.getvalue()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
        raise HTTPException(status_code=422, detail="Image is invalid or unsafe") from exc

    object_id = str(uuid.uuid4())
    storage_path = f"users/{user.id}/chat-images/{object_id}.{extension}"
    await asyncio.to_thread(
        services.storage.put, storage_path, sanitized, stored_mime
    )
    expires_at = (datetime.now(UTC) + timedelta(hours=24)).isoformat()
    try:
        upload_id = await asyncio.to_thread(
            services.store.create_upload,
            user.id,
            storage_path=storage_path,
            mime_type=stored_mime,
            size_bytes=len(sanitized),
            expires_at=expires_at,
        )
    except Exception:
        await asyncio.to_thread(services.storage.delete, storage_path)
        raise
    preview_url = await asyncio.to_thread(
        services.storage.signed_url, storage_path, 600
    )
    return {
        "id": upload_id,
        "mime_type": stored_mime,
        "size_bytes": len(sanitized),
        "sha256": hashlib.sha256(sanitized).hexdigest(),
        "preview_url": preview_url,
        "expires_at": expires_at,
    }


@app.post("/v1/feedback", status_code=201)
async def record_feedback(
    payload: FeedbackRequest,
    request: Request,
    user: Annotated[CurrentUser, Depends(current_user)],
) -> dict[str, int]:
    services = _services(request)
    _require_consent(services, user)
    if payload.message_id and not await asyncio.to_thread(
        services.store.owns_message, user.id, payload.message_id
    ):
        raise HTTPException(status_code=404, detail="Message not found")
    try:
        feedback_id = await asyncio.to_thread(
            services.store.record_feedback,
            category=payload.category,
            comment=payload.comment,
            consent=True,
            user_id=user.id,
            message_id=payload.message_id,
            rating=payload.rating,
            language=payload.language,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"id": feedback_id}


@app.delete("/v1/account", status_code=204)
async def delete_account(
    request: Request,
    user: Annotated[CurrentUser, Depends(current_user)],
) -> None:
    services = _services(request)
    paths = await asyncio.to_thread(services.store.user_storage_paths, user.id)
    await asyncio.to_thread(_delete_paths, services.storage, paths)
    await asyncio.to_thread(services.store.delete_user_records, user.id)
    await services.auth.delete_user(user.identity.auth_user_id)


@app.post("/v1/turns")
async def create_turn(
    payload: TurnRequest,
    request: Request,
    user: Annotated[CurrentUser, Depends(current_user)],
) -> StreamingResponse:
    services = _services(request)
    _require_consent(services, user)
    if payload.mode not in MODE_PROFILES:
        raise HTTPException(status_code=422, detail="Unknown answer mode")
    if payload.clarification_style not in {"auto", "guided", "direct"}:
        raise HTTPException(status_code=422, detail="Unknown clarification style")
    try:
        conversation = await asyncio.to_thread(
            services.store.get_conversation,
            user.id,
            payload.conversation_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    limit = await asyncio.to_thread(
        services.store.check_rate_limit, user.id, payload.mode
    )
    if not limit.allowed:
        raise HTTPException(
            status_code=429,
            detail=limit.message or "Rate limit reached",
            headers={"Retry-After": "3"},
        )

    history_records = await asyncio.to_thread(
        services.store.list_messages,
        user.id,
        payload.conversation_id,
        limit=24,
    )
    history = [
        {"role": item["role"], "content": item["content"]}
        for item in history_records
        if item["role"] in {"user", "assistant"}
    ]
    model_attachments: list[dict[str, Any]] = []
    stored_attachments: list[dict[str, Any]] = []
    for upload_id in payload.attachment_ids[:1]:
        try:
            upload = await asyncio.to_thread(
                services.store.get_upload, user.id, upload_id
            )
            data = await asyncio.to_thread(
                services.storage.get, upload["storage_path"]
            )
        except (ValueError, FileNotFoundError) as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        encoded = base64.b64encode(data).decode("ascii")
        model_attachments.append(
            {
                "kind": "image",
                "data_url": f"data:{upload['mime_type']};base64,{encoded}",
            }
        )
        stored_attachments.append(
            {
                "kind": "image",
                "storage_path": upload["storage_path"],
                "mime_type": upload["mime_type"],
                "size_bytes": upload["size_bytes"],
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )

    language = detect_language(payload.text)
    user_message_id = await asyncio.to_thread(
        services.store.add_message,
        user.id,
        payload.conversation_id,
        role="user",
        content=payload.text,
        language=language,
        attachments=stored_attachments,
    )
    for upload_id in payload.attachment_ids[:1]:
        await asyncio.to_thread(
            services.store.consume_upload, user.id, upload_id
        )
    if conversation["title"] == "New conversation":
        await asyncio.to_thread(
            services.store.rename_conversation,
            user.id,
            payload.conversation_id,
            payload.text[:80],
        )

    project_id = conversation.get("project_id")
    project_chunks: list[dict[str, Any]] = []
    project_instructions = ""
    if project_id:
        project_chunks = await asyncio.to_thread(
            services.store.list_project_chunks, user.id, project_id
        )
        project = await asyncio.to_thread(
            services.store.get_project, user.id, project_id
        )
        project_instructions = str(project.get("instructions") or "")
    artifact_service = ArtifactService(
        services.store,
        services.storage,
        owner_user_id=user.id,
        project_id=project_id,
        conversation_id=payload.conversation_id,
    )
    tools = ToolRegistry(
        services.knowledge,
        services.store,
        project_chunks=project_chunks,
        trusted_client=services.trusted,
        artifact_service=artifact_service,
    )
    clarification_count = await asyncio.to_thread(
        services.store.consecutive_clarifications,
        user.id,
        payload.conversation_id,
    )
    assistant_request = AssistantRequest(
        user_id=user.id,
        channel="web",
        conversation_id=payload.conversation_id,
        project_id=project_id,
        text=payload.text,
        attachments=tuple(model_attachments),
        mode=payload.mode,
        model_id=payload.model_id,
        clarification_style=payload.clarification_style,
        project_instructions=project_instructions,
    )
    turn_id = await asyncio.to_thread(
        services.store.create_assistant_turn,
        user.id,
        payload.conversation_id,
        user_message_id=user_message_id,
        clarification_count=clarification_count,
    )
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())

    async def event_stream() -> AsyncIterator[bytes]:
        turn_started = time.perf_counter()
        completed = False
        yield _sse(
            "turn.accepted",
            {"turn_id": turn_id, "request_id": request_id},
        )
        yield _sse("status", {"stage": "analysis_and_retrieval"})
        try:
            prepared = await services.pipeline.prepare(
                assistant_request,
                tools=tools,
                history=history,
                clarification_count=clarification_count,
            )
            async for event in services.pipeline.stream(
                assistant_request,
                prepared,
                tools=tools,
                history=history,
            ):
                if event.result is not None:
                    result = event.result
                    result.duration_ms = int(
                        (time.perf_counter() - turn_started) * 1000
                    )
                    assistant_message_id = await asyncio.to_thread(
                        services.store.add_message,
                        user.id,
                        payload.conversation_id,
                        role="assistant",
                        content=result.content,
                        language=result.language,
                        mode=payload.mode,
                        model=result.model,
                        status=result.kind,
                        citations=result.citations,
                        tools=result.tools_used,
                        artifact_ids=result.artifact_ids,
                        warning=(result.warnings[0] if result.warnings else None),
                    )
                    status = (
                        "failed"
                        if not result.success
                        else (
                            "awaiting_clarification"
                            if result.kind == "clarification"
                            else "complete"
                        )
                    )
                    await asyncio.to_thread(
                        services.store.complete_assistant_turn,
                        user.id,
                        turn_id,
                        status=status,
                        analysis=prepared.analysis.to_dict(),
                        assistant_message_id=assistant_message_id,
                        error_type=result.error_type,
                    )
                    await asyncio.to_thread(
                        services.store.complete_query,
                        user.id,
                        mode=payload.mode,
                        language=result.language,
                        duration_ms=result.duration_ms,
                        success=result.success,
                        error_type=result.error_type,
                        trusted_searches=(
                            1 if "search_trusted_sources" in result.tools_used else 0
                        ),
                        request_id=request_id,
                        ttft_ms=result.ttft_ms,
                        stage_durations=result.stage_durations,
                        prompt_tokens=result.prompt_tokens,
                        completion_tokens=result.completion_tokens,
                        estimated_cost_usd=result.estimated_cost_usd,
                    )
                    event.data["message_id"] = assistant_message_id
                    completed = True
                yield _sse(event.event, event.data)
        except asyncio.CancelledError:
            await asyncio.to_thread(
                services.store.complete_assistant_turn,
                user.id,
                turn_id,
                status="cancelled",
                analysis={},
                error_type="client_cancelled",
            )
            raise
        except Exception as exc:
            await asyncio.to_thread(
                services.store.complete_assistant_turn,
                user.id,
                turn_id,
                status="failed",
                analysis={},
                error_type=type(exc).__name__,
            )
            yield _sse(
                "error",
                {
                    "code": "internal_error",
                    "message": "The request could not be completed.",
                },
            )
        finally:
            if not completed:
                await asyncio.to_thread(
                    services.store.complete_query,
                    user.id,
                    mode=payload.mode,
                    language=language,
                    duration_ms=int((time.perf_counter() - turn_started) * 1000),
                    success=False,
                    error_type="incomplete_stream",
                    request_id=request_id,
                    stage_durations={},
                )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
