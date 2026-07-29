"""Authenticated Streamlit workspace for the RAISE internal pilot."""

from __future__ import annotations

import base64
import io
import os
import time
import uuid
from dataclasses import replace
from pathlib import Path
from typing import Any

import streamlit as st
from dotenv import load_dotenv
from PIL import Image

from .artifacts import ArtifactService
from .auth import IdentityError, UserIdentity, current_streamlit_identity
from .config import (
    AUTH_MODE,
    MAX_CHAT_IMAGE_BYTES,
    MODE_PROFILES,
    RETENTION_DAYS,
)
from .deployment_guard import validate_web_runtime
from .documents import DocumentService
from .knowledge import KnowledgeIndex
from .language import detect_language
from .llm import AssistantRequest, AssistantService
from .pilot_store import PilotStore
from .retention import purge_expired_content
from .storage_backends import PrivateFileStorage, configured_file_storage
from .tools import ToolRegistry
from .trusted_sources import TrustedSourceClient
from .voice import EDGE_TTS_AVAILABLE, synthesize_edge

load_dotenv()

CLARIFICATION_STYLES = {
    "auto": "Auto / تلقائي",
    "guided": "Guided / إرشاد خطوة بخطوة",
    "direct": "Direct / مباشر",
}


@st.cache_resource(show_spinner="Preparing the bilingual pilot workspace…")
def get_services() -> tuple[
    KnowledgeIndex,
    PilotStore,
    PrivateFileStorage,
    TrustedSourceClient,
]:
    validate_web_runtime()
    knowledge = KnowledgeIndex.from_directory()
    pilot_store = PilotStore(
        database_url=os.getenv("DATABASE_URL", ""),
        sqlite_path=os.getenv(
            "LOCAL_PILOT_DB_PATH",
            os.getenv("RUNTIME_DB_PATH", "data/pilot.sqlite3"),
        ),
    )
    file_storage = configured_file_storage()
    purge_expired_content(pilot_store, RETENTION_DAYS, file_storage)
    trusted_client = TrustedSourceClient(
        os.getenv("OPENROUTER_API_KEY"),
        enabled=os.getenv("ENABLE_TRUSTED_WEB_SEARCH", "false").lower() == "true",
    )
    return knowledge, pilot_store, file_storage, trusted_client


def _mode_label(key: str) -> str:
    profile = MODE_PROFILES[key]
    return f"{profile.label_en} / {profile.label_ar}"


def _init_state() -> None:
    defaults = {
        "conversation_id": None,
        "project_id": None,
        "pending_prompt": None,
        "remaining_queries": 30,
        "image_uploader_version": 0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_login() -> None:
    st.title("🌿 RAISE Farmer Assistant")
    st.subheader("ESDU internal pilot / النسخة التجريبية الداخلية")
    st.write(
        "Sign in with a verified Google account to access your private pilot "
        "workspace. No password is stored by this application."
    )
    st.button(
        "Continue with Google",
        type="primary",
        on_click=st.login,
        use_container_width=True,
    )


def ensure_identity(store: PilotStore) -> tuple[UserIdentity, dict[str, Any]] | None:
    try:
        identity = current_streamlit_identity(st)
    except IdentityError as exc:
        st.error(str(exc))
        if AUTH_MODE == "google":
            st.button("Log out", on_click=st.logout)
        st.stop()
        return None
    if identity is None:
        render_login()
        st.stop()
        return None
    user = store.upsert_user(identity)
    identity = replace(identity, user_id=user["id"])
    if identity.is_development and not store.has_current_consent(identity.user_id):
        store.accept_consent(identity.user_id)
        user = store.get_user(identity.user_id)
    return identity, user


def render_consent(identity: UserIdentity, store: PilotStore) -> None:
    if store.has_current_consent(identity.user_id):
        return
    st.title("Pilot consent / الموافقة على الاختبار")
    st.warning(
        "Use only public or non-sensitive agricultural information. Questions, "
        "project files, answer metadata, and feedback may be processed by configured "
        "cloud providers and retained for 30 days for the internal pilot."
    )
    accepted = st.checkbox(
        "I understand the pilot limits and consent to this processing and retention."
    )
    if st.button("Accept and continue", type="primary", disabled=not accepted):
        store.accept_consent(identity.user_id)
        st.rerun()
    if AUTH_MODE == "google":
        st.button("Log out", on_click=st.logout)
    st.stop()


def _delete_paths(storage: PrivateFileStorage, paths: list[str]) -> None:
    for path in paths:
        try:
            storage.delete(path)
        except Exception:  # noqa: BLE001, S112 - continue deleting owned files
            continue


def render_project_manager(
    identity: UserIdentity,
    store: PilotStore,
    storage: PrivateFileStorage,
) -> str | None:
    projects = store.list_projects(identity.user_id)
    project_options = [None, *[project["id"] for project in projects]]
    project_by_id = {project["id"]: project for project in projects}
    if st.session_state.project_id not in project_options:
        st.session_state.project_id = None
    selected_index = project_options.index(st.session_state.project_id)
    selected = st.selectbox(
        "Project / المشروع",
        project_options,
        index=selected_index,
        format_func=lambda item: (
            "No project / بدون مشروع" if item is None else project_by_id[item]["name"]
        ),
        key="project_selector",
    )
    if selected != st.session_state.project_id:
        st.session_state.project_id = selected
        st.session_state.conversation_id = None
        st.rerun()

    with st.expander("Create project / إنشاء مشروع"):
        with st.form("create_project_form", clear_on_submit=True):
            name = st.text_input("Project name")
            instructions = st.text_area(
                "Project instructions",
                help="These instructions cannot override safety or system rules.",
            )
            if st.form_submit_button("Create"):
                try:
                    project_id = store.create_project(
                        identity.user_id,
                        name,
                        instructions,
                    )
                    st.session_state.project_id = project_id
                    st.session_state.conversation_id = None
                    st.rerun()
                except ValueError as exc:
                    st.warning(str(exc))

    if selected:
        project = store.get_project(identity.user_id, selected)
        with st.expander("Project settings and files"):
            with st.form(f"edit_project_{selected}"):
                name = st.text_input("Name", value=project["name"])
                instructions = st.text_area(
                    "Instructions",
                    value=project["instructions"],
                )
                if st.form_submit_button("Save project"):
                    store.update_project(
                        identity.user_id,
                        selected,
                        name=name,
                        instructions=instructions,
                    )
                    st.success("Project saved.")

            uploader = st.file_uploader(
                "Add public/non-sensitive reference files",
                type=["pdf", "docx", "txt", "csv", "xlsx"],
                accept_multiple_files=True,
                key=f"project_upload_{selected}",
            )
            if uploader and st.button("Process files", key=f"process_{selected}"):
                service = DocumentService(store, storage)
                uploaded = 0
                for item in uploader:
                    try:
                        service.ingest(
                            identity.user_id,
                            selected,
                            filename=item.name,
                            data=item.getvalue(),
                            mime_type=item.type,
                        )
                        uploaded += 1
                    except (ValueError, RuntimeError) as exc:
                        st.warning(f"{item.name}: {exc}")
                if uploaded:
                    st.success(f"Processed {uploaded} file(s).")
                    st.rerun()

            documents = store.list_documents(identity.user_id, selected)
            for document in documents:
                col_name, col_delete = st.columns([4, 1])
                col_name.caption(
                    f"{document['filename']} · {document['size_bytes'] // 1024} KB"
                )
                if col_delete.button(
                    "Delete",
                    key=f"delete_doc_{document['id']}",
                ):
                    DocumentService(store, storage).delete(
                        identity.user_id,
                        selected,
                        document["id"],
                    )
                    st.rerun()

            st.divider()
            if st.button(
                "Delete project and its private files",
                key=f"delete_project_{selected}",
            ):
                paths = store.delete_project(identity.user_id, selected)
                _delete_paths(storage, paths)
                st.session_state.project_id = None
                st.session_state.conversation_id = None
                st.rerun()
    return selected


def ensure_conversation(
    identity: UserIdentity,
    store: PilotStore,
    project_id: str | None,
) -> str:
    conversation_id = st.session_state.conversation_id
    if conversation_id:
        try:
            conversation = store.get_conversation(identity.user_id, conversation_id)
            if conversation.get("project_id") == project_id:
                return conversation_id
        except ValueError:
            pass
    conversations = store.list_conversations(
        identity.user_id,
        project_id=project_id,
    )
    if conversations:
        conversation_id = conversations[0]["id"]
    else:
        conversation_id = store.create_conversation(
            identity.user_id,
            project_id=project_id,
        )
    st.session_state.conversation_id = conversation_id
    return conversation_id


def render_conversation_manager(
    identity: UserIdentity,
    store: PilotStore,
    storage: PrivateFileStorage,
    project_id: str | None,
) -> str:
    if st.button("＋ New chat / محادثة جديدة", use_container_width=True):
        st.session_state.conversation_id = store.create_conversation(
            identity.user_id,
            project_id=project_id,
        )
        st.rerun()
    search = st.text_input("Search chats", key="chat_search")
    conversations = store.list_conversations(
        identity.user_id,
        project_id=project_id,
        search=search,
    )
    conversation_id = ensure_conversation(identity, store, project_id)
    for conversation in conversations[:30]:
        label = conversation["title"]
        if st.button(
            label,
            key=f"conversation_{conversation['id']}",
            type=("primary" if conversation["id"] == conversation_id else "secondary"),
            use_container_width=True,
        ):
            st.session_state.conversation_id = conversation["id"]
            st.rerun()

    current = store.get_conversation(identity.user_id, conversation_id)
    with st.expander("Current chat settings"):
        with st.form(f"rename_{conversation_id}"):
            title = st.text_input("Chat title", value=current["title"])
            if st.form_submit_button("Rename"):
                store.rename_conversation(identity.user_id, conversation_id, title)
                st.rerun()
        if st.button("Archive chat", key=f"archive_chat_{conversation_id}"):
            store.archive_conversation(identity.user_id, conversation_id)
            st.session_state.conversation_id = None
            st.rerun()
        if st.button("Delete chat", key=f"delete_chat_{conversation_id}"):
            paths = store.delete_conversation(identity.user_id, conversation_id)
            _delete_paths(storage, paths)
            st.session_state.conversation_id = None
            st.rerun()
    return conversation_id


def render_sidebar(
    identity: UserIdentity,
    user: dict[str, Any],
    store: PilotStore,
    storage: PrivateFileStorage,
) -> tuple[str, str, str | None, str]:
    with st.sidebar:
        st.markdown("## RAISE 🌿")
        st.caption(f"{identity.name} · {identity.email or 'WhatsApp identity'}")
        if identity.is_admin:
            st.caption("Pilot administrator")
        if AUTH_MODE == "google":
            st.button("Log out", on_click=st.logout, use_container_width=True)

        configured_mode = user.get("default_mode", "standard")
        if configured_mode not in MODE_PROFILES:
            configured_mode = "standard"
        mode_key = st.selectbox(
            "Answer mode / نمط الإجابة",
            list(MODE_PROFILES),
            index=list(MODE_PROFILES).index(configured_mode),
            format_func=_mode_label,
        )
        configured_style = user.get("clarification_style", "auto")
        if configured_style not in CLARIFICATION_STYLES:
            configured_style = "auto"
        clarification_style = st.selectbox(
            "Conversation style / أسلوب المحادثة",
            list(CLARIFICATION_STYLES),
            index=list(CLARIFICATION_STYLES).index(configured_style),
            format_func=CLARIFICATION_STYLES.get,
        )
        profile = MODE_PROFILES[mode_key]
        st.caption(
            f"{profile.description} Model: `{profile.model}` · "
            f"reasoning: `{profile.reasoning_effort}`"
        )
        st.metric("Queries remaining today", st.session_state.remaining_queries)

        st.divider()
        project_id = render_project_manager(identity, store, storage)
        st.divider()
        conversation_id = render_conversation_manager(
            identity,
            store,
            storage,
            project_id,
        )
        if identity.is_admin:
            with st.expander("Pilot metrics"):
                performance = store.performance_summary()
                feedback = store.feedback_summary()
                st.json({**performance, **feedback})
    return mode_key, clarification_style, project_id, conversation_id


def render_citations(citations: list[dict[str, Any]]) -> None:
    if not citations:
        return
    with st.expander(f"📚 Evidence and sources ({len(citations)})"):
        for citation in citations:
            source_type = citation.get("source_type")
            if source_type == "raise_knowledge":
                st.markdown(
                    f"**[{citation.get('item_id')}] {citation.get('title')}**  \n"
                    f"Status: `{citation.get('status')}` · "
                    f"Evidence: `{citation.get('evidence_class')}`"
                )
                links = []
                for source in citation.get("sources") or []:
                    if source.get("url"):
                        links.append(
                            f"[{source.get('source_id')}]({source.get('url')})"
                        )
                if links:
                    st.markdown(" · ".join(links))
            elif source_type == "user_project_document":
                st.markdown(
                    f"**User document: {citation.get('title')}**  \n"
                    "_User-provided; not approved authority._"
                )
            elif source_type == "trusted_live":
                url = citation.get("url")
                title = citation.get("title") or citation.get("domain") or url
                if url:
                    st.markdown(f"**Trusted live source:** [{title}]({url})")
                else:
                    st.write(title)
            else:
                url = citation.get("url")
                title = citation.get("title") or citation.get("domain") or url
                if url:
                    st.markdown(f"**Model-provided link:** [{title}]({url})")
                else:
                    st.write(title)
            st.divider()


def render_artifacts(
    identity: UserIdentity,
    store: PilotStore,
    storage: PrivateFileStorage,
    artifact_ids: list[str],
) -> None:
    for artifact_id in artifact_ids:
        try:
            artifact = store.get_artifact(identity.user_id, artifact_id)
            signed_url = storage.signed_url(artifact["storage_path"], 600)
            if signed_url:
                st.link_button(
                    "Download " + artifact["filename"],
                    signed_url,
                    use_container_width=True,
                )
                continue
            data = storage.get(artifact["storage_path"])
        except (ValueError, FileNotFoundError, RuntimeError):
            st.warning("A generated artifact is no longer available.")
            continue
        st.download_button(
            f"Download {artifact['filename']}",
            data=data,
            file_name=artifact["filename"],
            mime=artifact["mime_type"],
            key=f"download_{artifact_id}",
        )


def render_message_feedback(
    identity: UserIdentity,
    store: PilotStore,
    message: dict[str, Any],
) -> None:
    columns = st.columns([1, 1, 6])
    if columns[0].button("👍", key=f"helpful_{message['id']}"):
        store.record_feedback(
            user_id=identity.user_id,
            message_id=message["id"],
            category="helpful",
            comment="Helpful answer",
            consent=True,
            rating=5,
            language=message.get("language"),
        )
        st.toast("Feedback recorded.")
    if columns[1].button("👎", key=f"not_helpful_{message['id']}"):
        store.record_feedback(
            user_id=identity.user_id,
            message_id=message["id"],
            category="not_helpful",
            comment="Answer needs improvement",
            consent=True,
            rating=1,
            language=message.get("language"),
        )
        st.toast("Feedback recorded.")
    with st.popover("Copy"):
        st.code(message["content"], language=None)


def render_audio(message: dict[str, Any]) -> None:
    if not EDGE_TTS_AVAILABLE:
        return
    with st.popover("🔊 Online voice / صوت عبر الإنترنت"):
        st.caption("This sends answer text to Microsoft Edge TTS.")
        if st.button("Generate audio", key=f"audio_{message['id']}"):
            try:
                st.audio(
                    synthesize_edge(
                        message["content"],
                        message.get("language") or detect_language(message["content"]),
                    )
                )
            except Exception:  # noqa: BLE001 - optional provider boundary
                st.warning("Audio could not be generated.")


def render_history(
    identity: UserIdentity,
    store: PilotStore,
    storage: PrivateFileStorage,
    conversation_id: str,
) -> list[dict[str, Any]]:
    messages = store.list_messages(identity.user_id, conversation_id)
    for message in messages:
        avatar = "🌿" if message["role"] == "assistant" else None
        with st.chat_message(message["role"], avatar=avatar):
            for attachment in message.get("attachments") or []:
                if attachment.get("kind") == "image" and attachment.get("storage_path"):
                    try:
                        st.image(storage.get(attachment["storage_path"]), width=320)
                    except (FileNotFoundError, RuntimeError):
                        st.caption("Attached image is unavailable.")
            if message.get("warning"):
                st.warning(message["warning"])
            st.markdown(message["content"])
            if message["role"] == "assistant":
                render_citations(message.get("citations") or [])
                if message.get("tools"):
                    st.caption("Tools used: " + ", ".join(message["tools"]))
                render_artifacts(
                    identity,
                    store,
                    storage,
                    message.get("artifact_ids") or [],
                )
                render_message_feedback(identity, store, message)
                render_audio(message)
    return messages


def _prepare_chat_image(
    identity: UserIdentity,
    conversation_id: str,
    upload: Any,
    storage: PrivateFileStorage,
) -> tuple[dict[str, Any], dict[str, Any]] | tuple[None, None]:
    if not upload:
        return None, None
    data = upload.getvalue()
    if not data or len(data) > MAX_CHAT_IMAGE_BYTES:
        raise ValueError("Image must be non-empty and no larger than 5 MB")
    if upload.type not in {"image/jpeg", "image/png"}:
        raise ValueError("Only JPG and PNG chat images are accepted")
    try:
        image = Image.open(io.BytesIO(data))
        image.verify()
    except Exception as exc:
        raise ValueError("Image file is invalid") from exc
    extension = ".png" if upload.type == "image/png" else ".jpg"
    storage_path = (
        f"users/{identity.user_id}/conversations/{conversation_id}/images/"
        f"{uuid.uuid4()}{extension}"
    )
    storage.put(storage_path, data, upload.type)
    persisted = {
        "kind": "image",
        "filename": Path(upload.name).name[:180],
        "mime_type": upload.type,
        "storage_path": storage_path,
        "size_bytes": len(data),
    }
    model_input = {
        "kind": "image",
        "data_url": f"data:{upload.type};base64,{base64.b64encode(data).decode('ascii')}",
    }
    return persisted, model_input


def main() -> None:
    st.set_page_config(
        page_title="RAISE ESDU Farmer Assistant",
        page_icon="🌿",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _init_state()
    knowledge, store, storage, trusted_client = get_services()
    identity_result = ensure_identity(store)
    if not identity_result:
        return
    identity, user = identity_result
    render_consent(identity, store)
    mode_key, clarification_style, project_id, conversation_id = render_sidebar(
        identity,
        user,
        store,
        storage,
    )

    st.title("🌿 RAISE Farmer Assistant")
    st.markdown(
        "**Akkar and rural Lebanon · عكار وريف لبنان**  \n"
        "Locally grounded agricultural, scientific, and rural-enterprise support."
    )
    st.info(
        "Internal pilot: verify high-risk agronomic, pesticide, veterinary, "
        "food-safety, financial, water-quality, and engineering decisions with a "
        "qualified local expert."
    )

    messages = render_history(identity, store, storage, conversation_id)
    if messages and messages[-1]["role"] == "assistant":
        previous_user = next(
            (
                message["content"]
                for message in reversed(messages[:-1])
                if message["role"] == "user"
            ),
            None,
        )
        if previous_user and st.button("Regenerate last answer"):
            st.session_state.pending_prompt = previous_user
            st.rerun()

    with st.expander("Attach a crop/farm image / أرفق صورة", expanded=False):
        chat_image = st.file_uploader(
            "JPG or PNG, maximum 5 MB; no definitive diagnosis is made from an image.",
            type=["jpg", "jpeg", "png"],
            key=f"chat_image_{st.session_state.image_uploader_version}",
        )

    user_input = st.chat_input(
        "Ask naturally; the assistant will clarify only when needed… / اسأل بطريقتك…"
    )
    if st.session_state.pending_prompt:
        user_input = st.session_state.pending_prompt
        st.session_state.pending_prompt = None

    if not user_input:
        if not messages:
            st.markdown("#### Try a question / جرّب سؤالاً")
            suggestions = [
                "Create a field checklist before planting potatoes in Akkar.",
                "اشرح لي كيف أحسب كلفة مشروع زراعي صغير ونقطة التعادل.",
                "What scientific evidence supports rainwater harvesting for livestock?",
                "الخيار في البيت البلاستيكي يذبل، ما المعلومات التي تحتاجها؟",
            ]
            columns = st.columns(2)
            for index, suggestion in enumerate(suggestions):
                if columns[index % 2].button(
                    suggestion,
                    key=f"suggestion_{index}",
                    use_container_width=True,
                ):
                    st.session_state.pending_prompt = suggestion
                    st.rerun()
        return

    rate = store.check_rate_limit(identity.user_id, mode_key)
    st.session_state.remaining_queries = rate.remaining_user
    if not rate.allowed:
        st.warning(rate.message)
        return

    persisted_attachment = None
    model_attachment = None
    try:
        persisted_attachment, model_attachment = _prepare_chat_image(
            identity,
            conversation_id,
            chat_image,
            storage,
        )
    except ValueError as exc:
        st.warning(str(exc))
        return

    prior_history = [
        {"role": message["role"], "content": message["content"]}
        for message in messages[-12:]
    ]
    store.add_message(
        identity.user_id,
        conversation_id,
        role="user",
        content=user_input,
        language=detect_language(user_input),
        attachments=[persisted_attachment] if persisted_attachment else [],
    )
    conversation = store.get_conversation(identity.user_id, conversation_id)
    if conversation["title"] == "New conversation":
        store.rename_conversation(
            identity.user_id,
            conversation_id,
            user_input[:80],
        )

    project_chunks = []
    project_instructions = ""
    if project_id:
        project_chunks = store.list_project_chunks(identity.user_id, project_id)
        project_instructions = store.get_project(
            identity.user_id,
            project_id,
        ).get("instructions", "")
    artifact_service = ArtifactService(
        store,
        storage,
        owner_user_id=identity.user_id,
        project_id=project_id,
        conversation_id=conversation_id,
    )
    tools = ToolRegistry(
        knowledge,
        store,
        project_chunks=project_chunks,
        trusted_client=trusted_client,
        artifact_service=artifact_service,
    )
    service = AssistantService(knowledge, tools)
    request = AssistantRequest(
        user_id=identity.user_id,
        channel="web",
        conversation_id=conversation_id,
        project_id=project_id,
        text=user_input,
        attachments=((model_attachment,) if model_attachment else ()),
        mode=mode_key,
        clarification_style=clarification_style,
        project_instructions=project_instructions,
    )
    with st.spinner("Understanding the need and checking relevant evidence…"):
        started = time.perf_counter()
        response = service.answer_request(
            request,
            conversation_history=prior_history,
        )
        elapsed_ms = int((time.perf_counter() - started) * 1000)

    store.add_message(
        identity.user_id,
        conversation_id,
        role="assistant",
        content=response.answer,
        language=response.language,
        mode=response.mode,
        model=response.model,
        status=response.kind,
        citations=response.citations,
        tools=response.tool_names,
        artifact_ids=response.artifact_ids,
        warning=response.warning,
    )
    store.complete_query(
        identity.user_id,
        mode=response.mode,
        language=response.language,
        duration_ms=elapsed_ms,
        success=response.success,
        error_type=response.error_type,
        trusted_searches=response.trusted_searches,
    )
    st.session_state.image_uploader_version += 1
    st.rerun()


if __name__ == "__main__":
    main()
