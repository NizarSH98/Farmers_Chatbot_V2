"""Authenticated FastAPI surface for the RAISE web workspace."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import os
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

import httpx
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
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

from .artifacts import ArtifactService
from .assistant_contracts import TURN_SCHEMA_VERSION, TurnCommand
from .assistant_pipeline import AssistantEngine
from .config import (
    APP_DISPLAY_NAME,
    APP_ENV,
    CONSENT_VERSION,
    MAX_CHAT_IMAGE_BYTES,
    MAX_PROJECT_FILE_BYTES,
    MODE_PROFILES,
    MODEL_CATALOG,
    OPENROUTER_ALLOWED_MODELS,
    RETENTION_DAYS,
    WEB_ALLOWED_ORIGINS,
)
from .deployment_guard import validate_web_runtime
from .documents import DocumentService
from .embedding_approval import EmbeddingApprovalError, load_embedding_approval
from .graph_repository import GraphRepository
from .image_processing import InvalidChatImage, sanitize_chat_image
from .language import detect_language
from .legal import agreement_markdown, agreement_markdown_ar
from .pilot_store import IdempotencyConflict, PilotStore, TurnReservation
from .provider import ProviderClient
from .qdrant_projection import ProjectionConfig, QdrantProjectionRepository
from .qdrant_retrieval import QdrantGraphRetrieval
from .release_knowledge import ReleaseKnowledgeGateway
from .retention import purge_expired_content
from .retrieval import PostgresGraphRetrieval, ProjectOnlyFallbackRetrieval
from .storage_backends import PrivateFileStorage, configured_file_storage
from .supabase_auth import (
    SupabaseAuthClient,
    SupabaseAuthError,
    SupabaseIdentity,
)
from .tools import ToolRegistry
from .trusted_sources import TrustedSourceClient
from .turn_coordinator import TurnCoordinator
from .whatsapp_router import router as whatsapp_router


@dataclass
class WebServices:
    store: PilotStore
    storage: PrivateFileStorage
    knowledge: ReleaseKnowledgeGateway
    trusted: TrustedSourceClient
    auth: SupabaseAuthClient
    pipeline: AssistantEngine
    coordinator: TurnCoordinator | None = None

    def __post_init__(self) -> None:
        if self.coordinator is None:
            self.coordinator = TurnCoordinator(self.store)


@dataclass(frozen=True)
class CurrentUser:
    record: dict[str, Any]
    identity: SupabaseIdentity

    @property
    def id(self) -> str:
        return str(self.record["id"])


class ConversationCreate(BaseModel):
    title: str = Field(default="New conversation", max_length=120)
    project_id: str | None = None


class ConversationUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=120)
    archived: bool | None = None


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    instructions: str = Field(default="", max_length=5000)


class ProjectUpdate(ProjectCreate):
    pass

class ClarificationSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid")

    interaction_id: str = Field(min_length=8, max_length=80)
    answers: dict[str, str | list[str]] = Field(min_length=1, max_length=3)

    @field_validator("answers")
    @classmethod
    def validate_answers(
        cls, answers: dict[str, str | list[str]]
    ) -> dict[str, str | list[str]]:
        cleaned: dict[str, str | list[str]] = {}
        for question_id, raw in answers.items():
            key = question_id.strip()
            if not key or len(key) > 40:
                raise ValueError("Invalid clarification question ID")
            values = raw if isinstance(raw, list) else [raw]
            normalized = [str(value).strip()[:500] for value in values]
            normalized = [value for value in normalized if value]
            if not normalized or len(normalized) > 6:
                raise ValueError("Each clarification answer must contain 1-6 values")
            cleaned[key] = normalized if isinstance(raw, list) else normalized[0]
        return cleaned




class TurnRequest(BaseModel):
    conversation_id: str
    text: str = Field(min_length=1, max_length=8000)
    mode: str = "standard"
    model_id: str | None = None
    clarification_style: str = "auto"
    attachment_ids: list[str] = Field(default_factory=list, max_length=1)
    clarification_response: ClarificationSubmission | None = None


class FeedbackRequest(BaseModel):
    category: str
    comment: str = Field(min_length=1, max_length=2000)
    rating: int | None = Field(default=None, ge=1, le=5)
    message_id: str | None = None
    language: str | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = validate_web_runtime()
    store = PilotStore(database_url=settings.database_url)
    storage = configured_file_storage()
    # Only project-owner-approved release content is eligible outside internal
    # scopes. Draft states stay reachable to editors through the admin APIs.
    review_statuses = (
        ("approved",)
        if APP_ENV in {"pilot", "production"}
        else ("approved", "field_review", "technical_review")
    )
    knowledge = ReleaseKnowledgeGateway(
        GraphRepository(store._connect),
        deployment_scope="production" if APP_ENV == "production" else "pilot",
        review_statuses=review_statuses,
    )
    trusted = TrustedSourceClient(
        settings.openrouter_api_key,
        enabled=os.getenv("ENABLE_TRUSTED_WEB_SEARCH", "false").lower() == "true",
    )
    auth = SupabaseAuthClient()
    provider = ProviderClient(api_key=settings.openrouter_api_key)
    retrieval = None
    rag_backend = os.getenv("RAG_BACKEND", "postgres").strip().lower()
    if rag_backend not in {"legacy", "postgres", "qdrant"}:
        raise RuntimeError("RAG_BACKEND must be one of legacy, postgres, or qdrant")
    if rag_backend != "legacy":
        vector_approved = (
            os.getenv("RAG_VECTOR_BENCHMARK_APPROVED", "false").lower() == "true"
        )
        embedding_model = os.getenv("RAG_EMBEDDING_MODEL") or None
        dimensions_value = os.getenv("RAG_EMBEDDING_DIMENSIONS") or ""
        embedding_dimensions = int(dimensions_value) if dimensions_value else None
        approval_sha256 = None
        if vector_approved and (
            not embedding_model or embedding_dimensions not in {768, 1536}
        ):
            raise RuntimeError(
                "Approved vector retrieval requires a benchmarked embedding model "
                "and RAG_EMBEDDING_DIMENSIONS=768 or 1536"
            )
        if vector_approved:
            report_path = os.getenv("RAG_EMBEDDING_BENCHMARK_REPORT", "").strip()
            expected_report_sha256 = os.getenv(
                "RAG_EMBEDDING_BENCHMARK_SHA256", ""
            ).strip()
            if not report_path or not expected_report_sha256:
                raise RuntimeError(
                    "Approved vector retrieval requires a benchmark report path "
                    "and checksum"
                )
            try:
                approval = load_embedding_approval(
                    report_path,
                    expected_sha256=expected_report_sha256,
                )
            except EmbeddingApprovalError as exc:
                raise RuntimeError(
                    f"Embedding benchmark approval is invalid: {exc}"
                ) from exc
            if (
                approval.model != embedding_model
                or approval.dimensions != embedding_dimensions
            ):
                raise RuntimeError(
                    "Configured embedding model/dimensions do not match the "
                    "approved benchmark candidate"
                )
            approval_sha256 = approval.report_sha256
        retrieval = PostgresGraphRetrieval(
            GraphRepository(store._connect),
            ProjectOnlyFallbackRetrieval(),
            provider,
            deployment_scope="production" if APP_ENV == "production" else "pilot",
            embedding_model=embedding_model,
            embedding_dimensions=embedding_dimensions,
            vector_approved=vector_approved,
            embedding_approval_sha256=approval_sha256,
        )
        if rag_backend == "qdrant":
            retrieval = QdrantGraphRetrieval(
                GraphRepository(store._connect),
                QdrantProjectionRepository(store._connect),
                retrieval,
                deployment_scope=("production" if APP_ENV == "production" else "pilot"),
                config=ProjectionConfig.from_env(),
            )
    pipeline = AssistantEngine(knowledge, provider=provider, retrieval=retrieval)
    services = WebServices(
        store, storage, knowledge, trusted, auth, pipeline, TurnCoordinator(store)
    )
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
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Idempotency-Key",
        "X-Request-ID",
    ],
)
app.include_router(whatsapp_router)


@app.middleware("http")
async def security_headers(request: Request, call_next: Any) -> Any:
    request_id = (
        request.headers.get("idempotency-key")
        or request.headers.get("x-request-id")
        or str(uuid.uuid4())
    )
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'none'; frame-ancestors 'none'"
    )
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
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
        raise HTTPException(
            status_code=428, detail="User agreement acceptance required"
        )


def _sse(event: str, data: dict[str, Any]) -> bytes:
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return f"event: {event}\ndata: {payload}\n\n".encode()


def _delete_paths(storage: PrivateFileStorage, paths: list[str]) -> None:
    for path in dict.fromkeys(paths):
        storage.delete(path)


@app.get("/healthz")
async def healthz(request: Request) -> dict[str, Any]:
    from .migration_status import EXPECTED_DATABASE_REVISION

    services = _services(request)
    result: dict[str, Any] = {
        "status": "ok",
        "service": "raise-web-api",
        "database_backend": "postgres",
        "expected_migration_revision": EXPECTED_DATABASE_REVISION,
        "rag_backend": os.getenv("RAG_BACKEND", "postgres").strip().lower(),
        "active_release_id": None,
        "projection_status": "not_configured",
        "qdrant_reachable": False,
        "fallback_ready": True,
        "local_model_available": False,
    }
    try:
        with services.store._connect() as connection:
            revision = connection.execute(
                "SELECT version_num FROM alembic_version"
            ).fetchone()
            active = connection.execute(
                """
                SELECT active.release_id, projection.state AS projection_state
                FROM active_knowledge_releases active
                LEFT JOIN knowledge_release_projections projection
                  ON projection.release_id=active.release_id
                 AND projection.target='qdrant'
                WHERE active.deployment_scope=%s
                """,
                ("production" if APP_ENV == "production" else "pilot",),
            ).fetchone()
        result["migration_revision"] = revision["version_num"] if revision else None
        result["active_release_id"] = active["release_id"] if active else None
        result["projection_status"] = (
            active.get("projection_state") if active else "missing"
        )
        result["fallback_ready"] = bool(active)
    except Exception:
        result["status"] = "degraded"
        result["fallback_ready"] = False
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6433").rstrip("/")
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    async with httpx.AsyncClient(timeout=2.0) as client:
        qdrant_check, ollama_check = await asyncio.gather(
            client.get(f"{qdrant_url}/collections"),
            client.get(f"{ollama_url}/api/tags"),
            return_exceptions=True,
        )
    result["qdrant_reachable"] = (
        isinstance(qdrant_check, httpx.Response) and qdrant_check.status_code == 200
    )
    result["local_model_available"] = (
        isinstance(ollama_check, httpx.Response) and ollama_check.status_code == 200
    )
    if result["rag_backend"] == "qdrant" and not result["qdrant_reachable"]:
        result["projection_status"] = "unreachable_fallback_ready"
    return result


@app.get("/v1/config")
async def public_config() -> dict[str, Any]:
    return {
        "app_name": APP_DISPLAY_NAME,
        "agreement_version": CONSENT_VERSION,
        "default_language": "ar",
        "corpus_warning": None,
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


@app.get("/v1/usage")
async def usage(
    request: Request,
    user: Annotated[CurrentUser, Depends(current_user)],
) -> dict[str, Any]:
    services = _services(request)
    weekly = await asyncio.to_thread(services.store.get_weekly_usage, user.id)
    return {
        "weekly_spend_usd": weekly.spend_usd,
        "weekly_limit_usd": weekly.limit_usd,
        "week_start": weekly.week_start,
        "week_end": weekly.week_end,
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


@app.get("/v1/projects")
async def list_projects(
    request: Request,
    user: Annotated[CurrentUser, Depends(current_user)],
) -> dict[str, Any]:
    services = _services(request)
    _require_consent(services, user)
    return {"items": await asyncio.to_thread(services.store.list_projects, user.id)}


@app.post("/v1/projects", status_code=201)
async def create_project(
    payload: ProjectCreate,
    request: Request,
    user: Annotated[CurrentUser, Depends(current_user)],
) -> dict[str, Any]:
    services = _services(request)
    _require_consent(services, user)
    try:
        project_id = await asyncio.to_thread(
            services.store.create_project,
            user.id,
            payload.name,
            instructions=payload.instructions,
        )
        return await asyncio.to_thread(services.store.get_project, user.id, project_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.patch("/v1/projects/{project_id}")
async def update_project(
    project_id: str,
    payload: ProjectUpdate,
    request: Request,
    user: Annotated[CurrentUser, Depends(current_user)],
) -> dict[str, Any]:
    services = _services(request)
    _require_consent(services, user)
    try:
        await asyncio.to_thread(
            services.store.update_project,
            user.id,
            project_id,
            name=payload.name,
            instructions=payload.instructions,
        )
        return await asyncio.to_thread(services.store.get_project, user.id, project_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.delete("/v1/projects/{project_id}", status_code=204)
async def delete_project(
    project_id: str,
    request: Request,
    user: Annotated[CurrentUser, Depends(current_user)],
) -> None:
    services = _services(request)
    _require_consent(services, user)
    try:
        paths = await asyncio.to_thread(
            services.store.delete_project, user.id, project_id
        )
        await asyncio.to_thread(_delete_paths, services.storage, paths)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/v1/projects/{project_id}/documents")
async def list_project_documents(
    project_id: str,
    request: Request,
    user: Annotated[CurrentUser, Depends(current_user)],
) -> dict[str, Any]:
    services = _services(request)
    _require_consent(services, user)
    try:
        items = await asyncio.to_thread(
            services.store.list_documents, user.id, project_id
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"items": items}


@app.post("/v1/projects/{project_id}/documents", status_code=201)
async def upload_project_document(
    project_id: str,
    request: Request,
    user: Annotated[CurrentUser, Depends(current_user)],
    document: Annotated[UploadFile, File()],
) -> dict[str, Any]:
    services = _services(request)
    _require_consent(services, user)
    data = await document.read(MAX_PROJECT_FILE_BYTES + 1)
    service = DocumentService(services.store, services.storage)
    try:
        document_id = await asyncio.to_thread(
            service.ingest,
            user.id,
            project_id,
            filename=document.filename or "document",
            data=data,
            mime_type=document.content_type,
        )
        items = await asyncio.to_thread(
            services.store.list_documents, user.id, project_id
        )
        return next(item for item in items if item["id"] == document_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/v1/projects/{project_id}/documents/{document_id}/download")
async def download_project_document(
    project_id: str,
    document_id: str,
    request: Request,
    user: Annotated[CurrentUser, Depends(current_user)],
) -> Response:
    services = _services(request)
    _require_consent(services, user)
    try:
        documents = await asyncio.to_thread(
            services.store.list_documents, user.id, project_id
        )
        document = next(item for item in documents if item["id"] == document_id)
        data = await asyncio.to_thread(services.storage.get, document["storage_path"])
    except (ValueError, StopIteration, FileNotFoundError) as exc:
        raise HTTPException(status_code=404, detail="Document not found") from exc
    filename = (
        str(document["filename"]).replace('"', "").replace("\r", "").replace("\n", "")
    )
    return Response(
        content=data,
        media_type=str(document["mime_type"]),
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.delete("/v1/projects/{project_id}/documents/{document_id}", status_code=204)
async def delete_project_document(
    project_id: str,
    document_id: str,
    request: Request,
    user: Annotated[CurrentUser, Depends(current_user)],
) -> None:
    services = _services(request)
    _require_consent(services, user)
    try:
        await asyncio.to_thread(
            DocumentService(services.store, services.storage).delete,
            user.id,
            project_id,
            document_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/v1/artifacts")
async def list_artifacts(
    request: Request,
    user: Annotated[CurrentUser, Depends(current_user)],
    project_id: str | None = None,
    conversation_id: str | None = None,
) -> dict[str, Any]:
    services = _services(request)
    _require_consent(services, user)
    items = await asyncio.to_thread(
        services.store.list_artifacts,
        user.id,
        project_id=project_id,
        conversation_id=conversation_id,
    )
    for item in items:
        item["metadata"] = json.loads(item.pop("metadata_json") or "{}")
    return {"items": items}


@app.get("/v1/artifacts/{artifact_id}/download")
async def download_artifact(
    artifact_id: str,
    request: Request,
    user: Annotated[CurrentUser, Depends(current_user)],
) -> Response:
    services = _services(request)
    _require_consent(services, user)
    try:
        artifact = await asyncio.to_thread(
            services.store.get_artifact, user.id, artifact_id
        )
        data = await asyncio.to_thread(services.storage.get, artifact["storage_path"])
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=404, detail="Artifact not found") from exc
    filename = (
        str(artifact["filename"]).replace('"', "").replace("\r", "").replace("\n", "")
    )
    return Response(
        content=data,
        media_type=str(artifact["mime_type"]),
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.delete("/v1/artifacts/{artifact_id}", status_code=204)
async def delete_artifact(
    artifact_id: str,
    request: Request,
    user: Annotated[CurrentUser, Depends(current_user)],
) -> None:
    services = _services(request)
    _require_consent(services, user)
    try:
        path = await asyncio.to_thread(
            services.store.delete_artifact, user.id, artifact_id
        )
        await asyncio.to_thread(services.storage.delete, path)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/v1/export")
async def export_workspace(
    request: Request,
    user: Annotated[CurrentUser, Depends(current_user)],
) -> dict[str, Any]:
    services = _services(request)
    _require_consent(services, user)
    return await asyncio.to_thread(services.store.export_user_data, user.id)


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
        project_id=payload.project_id,
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
        await asyncio.to_thread(
            services.store.get_conversation, user.id, conversation_id
        )
        await services.pipeline.clarification.delete(user.id, conversation_id)
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
    data = await image.read(MAX_CHAT_IMAGE_BYTES + 1)
    if not data or len(data) > MAX_CHAT_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image must be under 5 MB")
    try:
        normalized = sanitize_chat_image(data, supplied_mime)
    except InvalidChatImage as exc:
        status = 415 if supplied_mime not in {"image/jpeg", "image/png"} else 422
        raise HTTPException(status_code=status, detail=str(exc)) from exc
    sanitized = normalized.data
    stored_mime = normalized.mime_type
    extension = normalized.extension

    object_id = str(uuid.uuid4())
    storage_path = f"users/{user.id}/chat-images/{object_id}.{extension}"
    await asyncio.to_thread(services.storage.put, storage_path, sanitized, stored_mime)
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
    conversation_ids = await asyncio.to_thread(
        services.store.list_conversation_ids, user.id
    )
    for conversation_id in conversation_ids:
        await services.pipeline.clarification.delete(user.id, conversation_id)

    await asyncio.to_thread(services.store.delete_user_records, user.id)
    await services.auth.delete_user(user.identity.auth_user_id)


def _streaming_response(stream: AsyncIterator[bytes]) -> StreamingResponse:
    return StreamingResponse(
        stream,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


def _turn_wire_data(
    data: dict[str, Any],
    *,
    turn_id: str,
    request_id: str,
    sequence: int,
) -> dict[str, Any]:
    return {
        **data,
        "schema_version": TURN_SCHEMA_VERSION,
        "turn_id": turn_id,
        "request_id": request_id,
        "sequence": sequence,
    }


async def _replay_turn_stream(
    services: WebServices,
    user_id: str,
    reservation: TurnReservation,
) -> AsyncIterator[bytes]:
    turn_id = str(reservation.turn_id)
    state = await asyncio.to_thread(services.coordinator.status, user_id, turn_id)
    request_id = str(state.get("request_id") or "")
    yield _sse(
        "turn.accepted",
        _turn_wire_data(
            {"replayed": True},
            turn_id=turn_id,
            request_id=request_id,
            sequence=0,
        ),
    )
    if not state["terminal"]:
        yield _sse(
            "status",
            _turn_wire_data(
                {"stage": state["status"], "replayed": True},
                turn_id=turn_id,
                request_id=request_id,
                sequence=1,
            ),
        )
        return
    message = state.get("message") or {}
    sequence = max(1, int(state.get("terminal_sequence") or 1))
    yield _sse(
        "turn.completed",
        _turn_wire_data(
            {
                "kind": message.get("status") or state["status"],
                "model": message.get("model"),
                "message_id": message.get("id"),
                "content": message.get("content") or "",
                "outcome": state["status"],
                "replayed": True,
            },
            turn_id=turn_id,
            request_id=request_id,
            sequence=sequence,
        ),
    )


@app.get("/v1/turns/{turn_id}")
async def get_turn_status(
    turn_id: str,
    request: Request,
    user: Annotated[CurrentUser, Depends(current_user)],
) -> dict[str, Any]:
    services = _services(request)
    _require_consent(services, user)
    try:
        state = await asyncio.to_thread(services.coordinator.status, user.id, turn_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if state["terminal"] and state.get("error"):
        state["error"] = "The request could not be completed."
    return state


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
    request_id = (
        request.headers.get("idempotency-key")
        or request.headers.get("x-request-id")
        or str(uuid.uuid4())
    ).strip()
    if not request_id or len(request_id) > 200:
        raise HTTPException(status_code=422, detail="Invalid Idempotency-Key")
    try:
        conversation = await asyncio.to_thread(
            services.store.get_conversation, user.id, payload.conversation_id
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    project_id = conversation.get("project_id")
    attachment_references = tuple(
        {"upload_id": upload_id} for upload_id in payload.attachment_ids[:1]
    )
    command = TurnCommand(
        request_id=request_id,
        actor_id=user.id,
        channel="web",
        conversation_id=payload.conversation_id,
        project_id=project_id,
        text=payload.text,
        attachment_references=attachment_references,
        mode=payload.mode,
        clarification_response=(
            payload.clarification_response.model_dump(mode="json")
            if payload.clarification_response else None
        ),
        model_id=payload.model_id,
        clarification_style=payload.clarification_style,
    )
    try:
        replay = await asyncio.to_thread(services.coordinator.replay, command)
    except IdempotencyConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if replay:
        return _streaming_response(_replay_turn_stream(services, user.id, replay))

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
            data = await asyncio.to_thread(services.storage.get, upload["storage_path"])
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
    command = TurnCommand(
        request_id=request_id,
        actor_id=user.id,
        channel="web",
        conversation_id=payload.conversation_id,
        project_id=project_id,
        text=payload.text,
        attachments=tuple(model_attachments),
        attachment_references=attachment_references,
        mode=payload.mode,
        clarification_response=(
            payload.clarification_response.model_dump(mode="json")
            if payload.clarification_response else None
        ),
        model_id=payload.model_id,
        clarification_style=payload.clarification_style,
        project_instructions=project_instructions,
    )
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
    language = detect_language(payload.text)
    try:
        reservation = await asyncio.to_thread(
            services.coordinator.reserve,
            command,
            language=language,
            stored_attachments=stored_attachments,
            clarification_count=clarification_count,
        )
    except IdempotencyConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if not reservation.allowed:
        raise HTTPException(
            status_code=429,
            detail=reservation.message or "Rate limit reached",
            headers={"Retry-After": "3"},
        )
    if reservation.existing:
        return _streaming_response(_replay_turn_stream(services, user.id, reservation))
    turn_id = str(reservation.turn_id)
    for upload_id in payload.attachment_ids[:1]:
        await asyncio.to_thread(services.store.consume_upload, user.id, upload_id)
    if conversation["title"] == "New conversation":
        await asyncio.to_thread(
            services.store.rename_conversation,
            user.id,
            payload.conversation_id,
            payload.text[:80],
        )

    async def event_stream() -> AsyncIterator[bytes]:
        turn_started = time.perf_counter()
        sequence = 0
        finalized = False

        def encode(event: str, data: dict[str, Any]) -> bytes:
            nonlocal sequence
            wire = _turn_wire_data(
                data,
                turn_id=turn_id,
                request_id=request_id,
                sequence=sequence,
            )
            sequence += 1
            return _sse(event, wire)

        yield encode("turn.accepted", {})
        yield encode("status", {"stage": "analysis_and_retrieval"})
        try:
            prepared = await services.pipeline.prepare(
                command,
                tools=tools,
                history=history,
                clarification_count=clarification_count,
            )
            async for event in services.pipeline.stream(
                command,
                prepared,
                tools=tools,
                history=history,
            ):
                data = dict(event.data)
                if event.result is not None:
                    result = event.result
                    result.duration_ms = int(
                        (time.perf_counter() - turn_started) * 1000
                    )
                    assistant_message_id = await asyncio.to_thread(
                        services.coordinator.finalize,
                        command,
                        turn_id,
                        result,
                        analysis={
                            **prepared.analysis.to_dict(),
                            "retrieval": prepared.retrieval_metrics,
                            "graph_paths": prepared.graph_paths,
                        },
                        terminal_sequence=sequence,
                    )
                    data["message_id"] = assistant_message_id
                    finalized = True
                yield encode(event.event, data)
            if not finalized:
                await asyncio.to_thread(
                    services.coordinator.fail,
                    user.id,
                    turn_id,
                    status="failed",
                    error_type="incomplete_stream",
                    duration_ms=int((time.perf_counter() - turn_started) * 1000),
                    terminal_sequence=sequence,
                )
                finalized = True
                yield encode(
                    "error",
                    {
                        "code": "incomplete_stream",
                        "message": "The request could not be completed.",
                        "terminal": True,
                    },
                )
        except asyncio.CancelledError:
            if not finalized:
                await asyncio.to_thread(
                    services.coordinator.fail,
                    user.id,
                    turn_id,
                    status="cancelled",
                    error_type="client_cancelled",
                    duration_ms=int((time.perf_counter() - turn_started) * 1000),
                    terminal_sequence=sequence,
                )
            raise
        except Exception as exc:
            if not finalized:
                await asyncio.to_thread(
                    services.coordinator.fail,
                    user.id,
                    turn_id,
                    status="failed",
                    error_type=type(exc).__name__,
                    duration_ms=int((time.perf_counter() - turn_started) * 1000),
                    terminal_sequence=sequence,
                )
            yield encode(
                "error",
                {
                    "code": "internal_error",
                    "message": "The request could not be completed.",
                    "terminal": True,
                },
            )

    return _streaming_response(event_stream())


class ReleaseActionBody(BaseModel):
    deployment_scope: str = Field(
        default="pilot", pattern="^(internal|pilot|production)$"
    )


class EditorAssignmentBody(BaseModel):
    user_id: str = Field(min_length=1, max_length=200)


class ChangeProposalBody(BaseModel):
    base_release_id: str = Field(min_length=1, max_length=200)
    record_type: str = Field(pattern="^(document|claim|relation|translation)$")
    record_id: str = Field(min_length=1, max_length=300)
    operation: str = Field(pattern="^(create|update|retire)$")
    patch: dict[str, Any]


class ProposalReviewBody(BaseModel):
    state: str = Field(pattern="^(accepted|rejected)$")
    proposed_release_id: str | None = Field(default=None, max_length=200)
    review_note: str | None = Field(default=None, max_length=2000)


def _require_admin(user: CurrentUser) -> None:
    if user.record.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Administrator access required")


def _is_editor(services: WebServices, user: CurrentUser) -> bool:
    if user.record.get("role") == "admin":
        return True
    with services.store._connect() as connection:
        row = connection.execute(
            "SELECT 1 FROM knowledge_editors WHERE user_id=%s AND revoked_at IS NULL",
            (user.id,),
        ).fetchone()
    return row is not None


async def _activate_qdrant_aliases(
    services: WebServices, release_id: str
) -> dict[str, Any]:
    from .qdrant_projection import ProjectionManifest, QdrantProjector

    projection = await asyncio.to_thread(
        QdrantProjectionRepository(services.store._connect).projection, release_id
    )
    if not projection or projection.get("state") != "ready":
        raise HTTPException(
            status_code=409, detail="Release has no ready Qdrant projection"
        )
    manifest = ProjectionManifest(
        release_id=release_id,
        evidence_collection=str(projection["evidence_collection"]),
        entity_collection=str(projection["entity_collection"]),
        evidence_points=int(projection["evidence_points"]),
        entity_points=int(projection["entity_points"]),
        embedding_model=str(projection["embedding_model"]),
        embedding_dimensions=int(projection["embedding_dimensions"]),
        manifest_sha256=str(projection["manifest_sha256"]),
    )
    projector = QdrantProjector(
        QdrantProjectionRepository(services.store._connect),
        ProjectionConfig.from_env(),
    )
    try:
        await projector.activate_aliases(manifest)
    finally:
        await projector.close()
    return dict(projection)


@app.get("/v1/admin/knowledge/releases")
async def admin_list_releases(
    request: Request,
    user: Annotated[CurrentUser, Depends(current_user)],
) -> dict[str, Any]:
    _require_admin(user)
    services = _services(request)
    with services.store._connect() as connection:
        rows = connection.execute(
            """
            SELECT release.id, release.version, release.state,
                   release.publication_scope, release.review_policy,
                   release.embedding_model, release.embedding_dimensions,
                   release.source_manifest_sha256, release.created_at,
                   release.sealed_at, projection.state AS projection_state,
                   projection.evidence_points, projection.entity_points,
                   projection.manifest_sha256 AS projection_manifest_sha256,
                   array_remove(array_agg(active.deployment_scope), NULL) AS active_scopes
            FROM knowledge_releases release
            LEFT JOIN knowledge_release_projections projection
              ON projection.release_id=release.id AND projection.target='qdrant'
            LEFT JOIN active_knowledge_releases active ON active.release_id=release.id
            GROUP BY release.id, projection.state, projection.evidence_points,
                     projection.entity_points, projection.manifest_sha256
            ORDER BY release.created_at DESC
            """
        ).fetchall()
    return {"releases": [dict(row) for row in rows]}


@app.post("/v1/admin/knowledge/releases/{release_id}/activate")
async def admin_activate_release(
    release_id: str,
    body: ReleaseActionBody,
    request: Request,
    user: Annotated[CurrentUser, Depends(current_user)],
) -> dict[str, Any]:
    _require_admin(user)
    services = _services(request)
    projection = await _activate_qdrant_aliases(services, release_id)
    try:
        result = await asyncio.to_thread(
            GraphRepository(services.store._connect).activate_release,
            body.deployment_scope,
            release_id,
            activated_by=user.id,
        )
    except Exception as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {
        "deployment_scope": result.deployment_scope,
        "release_id": result.release_id,
        "previous_release_id": result.previous_release_id,
        "projection_manifest_sha256": projection["manifest_sha256"],
    }


@app.post("/v1/admin/knowledge/releases/rollback")
async def admin_rollback_release(
    body: ReleaseActionBody,
    request: Request,
    user: Annotated[CurrentUser, Depends(current_user)],
) -> dict[str, Any]:
    _require_admin(user)
    services = _services(request)
    with services.store._connect() as connection:
        current = connection.execute(
            "SELECT release_id FROM active_knowledge_releases WHERE deployment_scope=%s",
            (body.deployment_scope,),
        ).fetchone()
        if not current:
            raise HTTPException(
                status_code=409, detail="No active release to roll back"
            )
        target = connection.execute(
            """
            SELECT previous_release_id FROM knowledge_release_activations
            WHERE deployment_scope=%s AND release_id=%s
              AND previous_release_id IS NOT NULL
            ORDER BY activated_at DESC LIMIT 1
            """,
            (body.deployment_scope, current["release_id"]),
        ).fetchone()
    if not target:
        raise HTTPException(status_code=409, detail="No previous release is available")
    target_id = str(target["previous_release_id"])
    await _activate_qdrant_aliases(services, target_id)
    try:
        result = await asyncio.to_thread(
            GraphRepository(services.store._connect).rollback_release,
            body.deployment_scope,
            activated_by=user.id,
        )
    except Exception as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {
        "deployment_scope": result.deployment_scope,
        "release_id": result.release_id,
        "previous_release_id": result.previous_release_id,
        "rolled_back": result.rolled_back,
    }


@app.get("/v1/admin/knowledge/neighborhood")
async def admin_graph_neighborhood(
    request: Request,
    user: Annotated[CurrentUser, Depends(current_user)],
    query: str = Query(min_length=1, max_length=500),
    hops: int = Query(default=1, ge=1, le=2),
) -> dict[str, Any]:
    _require_admin(user)
    services = _services(request)
    repository = GraphRepository(services.store._connect)
    release_id = await asyncio.to_thread(repository.active_release, "pilot")
    if not release_id:
        raise HTTPException(status_code=404, detail="No active pilot release")
    entities = await asyncio.to_thread(
        repository.resolve_entities, release_id=release_id, query=query, limit=20
    )
    paths = await asyncio.to_thread(
        repository.graph_paths,
        release_id=release_id,
        entity_ids=tuple(str(row["id"]) for row in entities),
        max_hops=hops,
        review_statuses=("approved",),
        limit=100,
    )
    return {"release_id": release_id, "entities": entities, "paths": paths}


@app.post("/v1/admin/knowledge/editors")
async def admin_assign_editor(
    body: EditorAssignmentBody,
    request: Request,
    user: Annotated[CurrentUser, Depends(current_user)],
) -> dict[str, Any]:
    _require_admin(user)
    services = _services(request)
    with services.store._connect() as connection:
        row = connection.execute(
            "SELECT id FROM users WHERE id=%s", (body.user_id,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        connection.execute(
            """
            INSERT INTO knowledge_editors(user_id, assigned_by)
            VALUES (%s,%s)
            ON CONFLICT(user_id) DO UPDATE SET assigned_by=excluded.assigned_by,
                assigned_at=now(), revoked_at=NULL
            """,
            (body.user_id, user.id),
        )
    return {"user_id": body.user_id, "editor": True}


@app.post("/v1/editor/knowledge/proposals")
async def editor_create_proposal(
    body: ChangeProposalBody,
    request: Request,
    user: Annotated[CurrentUser, Depends(current_user)],
) -> dict[str, Any]:
    services = _services(request)
    if not await asyncio.to_thread(_is_editor, services, user):
        raise HTTPException(status_code=403, detail="Editor access required")
    proposal_id = f"proposal_{uuid.uuid4().hex}"
    with services.store._connect() as connection:
        base = connection.execute(
            "SELECT id FROM knowledge_releases WHERE id=%s",
            (body.base_release_id,),
        ).fetchone()
        if not base:
            raise HTTPException(status_code=404, detail="Base release not found")
        connection.execute(
            """
            INSERT INTO knowledge_change_proposals(
                id,base_release_id,editor_user_id,record_type,record_id,
                operation,patch_json
            ) VALUES (%s,%s,%s,%s,%s,%s,%s::jsonb)
            """,
            (
                proposal_id,
                body.base_release_id,
                user.id,
                body.record_type,
                body.record_id,
                body.operation,
                json.dumps(body.patch, ensure_ascii=False),
            ),
        )
    return {"proposal_id": proposal_id, "state": "proposed"}


@app.get("/v1/editor/knowledge/proposals")
async def editor_list_proposals(
    request: Request,
    user: Annotated[CurrentUser, Depends(current_user)],
    state: str | None = Query(
        default=None, pattern="^(proposed|accepted|rejected|superseded)$"
    ),
) -> dict[str, Any]:
    services = _services(request)
    if not await asyncio.to_thread(_is_editor, services, user):
        raise HTTPException(status_code=403, detail="Editor access required")
    with services.store._connect() as connection:
        rows = connection.execute(
            "SELECT * FROM knowledge_change_proposals WHERE (%s IS NULL OR state=%s) ORDER BY created_at DESC LIMIT 500",
            (state, state),
        ).fetchall()
    return {"proposals": [dict(row) for row in rows]}


@app.post("/v1/admin/knowledge/proposals/{proposal_id}/review")
async def admin_review_proposal(
    proposal_id: str,
    body: ProposalReviewBody,
    request: Request,
    user: Annotated[CurrentUser, Depends(current_user)],
) -> dict[str, Any]:
    _require_admin(user)
    services = _services(request)
    if body.state == "accepted" and not body.proposed_release_id:
        raise HTTPException(
            status_code=409,
            detail="Accepted changes must reference a separately built immutable release",
        )
    with services.store._connect() as connection:
        if body.proposed_release_id:
            release = connection.execute(
                "SELECT state FROM knowledge_releases WHERE id=%s",
                (body.proposed_release_id,),
            ).fetchone()
            if not release or release["state"] != "ready":
                raise HTTPException(
                    status_code=409, detail="Proposed release is not ready"
                )
        cursor = connection.execute(
            """
            UPDATE knowledge_change_proposals
            SET state=%s, proposed_release_id=%s, reviewer_user_id=%s,
                review_note=%s, reviewed_at=now()
            WHERE id=%s AND state='proposed'
            """,
            (
                body.state,
                body.proposed_release_id,
                user.id,
                body.review_note,
                proposal_id,
            ),
        )
        if cursor.rowcount != 1:
            raise HTTPException(status_code=409, detail="Proposal is not reviewable")
    return {"proposal_id": proposal_id, "state": body.state}
