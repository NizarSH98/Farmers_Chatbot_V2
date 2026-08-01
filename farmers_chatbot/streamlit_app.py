"""Authenticated Streamlit workspace for the RAISE-ESDU project."""

from __future__ import annotations

import base64
import io
import json
import os
import time
import uuid
from dataclasses import replace
from pathlib import Path
from typing import Any

import streamlit as st
from dotenv import load_dotenv
from PIL import Image, ImageOps

from .artifacts import ArtifactService
from .auth import IdentityError, UserIdentity, current_streamlit_identity
from .config import (
    APP_DISPLAY_NAME,
    APP_PUBLIC_URL,
    AUTH_MODE,
    CONSENT_VERSION,
    MAX_CHAT_IMAGE_BYTES,
    MODE_PROFILES,
    MODEL_CATALOG,
    OPENROUTER_ALLOWED_MODELS,
    OPENROUTER_DEFAULT_MODEL,
    PRIVACY_CONTACT_EMAIL,
    RETENTION_DAYS,
)
from .deployment_guard import validate_web_runtime
from .documents import DocumentService
from .knowledge import KnowledgeIndex
from .language import detect_language
from .legal import (
    agreement_markdown,
    agreement_markdown_ar,
    privacy_policy_markdown,
    privacy_policy_markdown_ar,
)
from .llm import AssistantRequest, AssistantService
from .pilot_store import PilotStore
from .retention import purge_expired_content
from .storage_backends import PrivateFileStorage, configured_file_storage
from .tools import ToolRegistry
from .trusted_sources import TrustedSourceClient
from .ui_copy import (
    DEFAULT_UI_LANGUAGE,
    MODEL_DESCRIPTION_KEYS,
    normalize_ui_language,
)
from .ui_copy import (
    text as ui_text,
)
from .voice import EDGE_TTS_AVAILABLE, synthesize_edge

load_dotenv()

CLARIFICATION_STYLES = ("auto", "guided", "direct")


@st.cache_resource(show_spinner="Preparing the bilingual workspace…")
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


def _t(key: str, **values: Any) -> str:
    return ui_text(
        st.session_state.get("ui_language", DEFAULT_UI_LANGUAGE), key, **values
    )


def _mode_label(key: str) -> str:
    return _t(f"mode_{key}")


def _model_label(model_id: str) -> str:
    option = MODEL_CATALOG[model_id]
    return option.label


def _clarification_label(key: str) -> str:
    return _t(f"style_{key}")


def _init_state() -> None:
    defaults = {
        "conversation_id": None,
        "project_id": None,
        "pending_prompt": None,
        "remaining_queries": 30,
        "image_uploader_version": 0,
        "ui_language": DEFAULT_UI_LANGUAGE,
        "active_mode": None,
        "active_model": None,
        "active_clarification_style": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _render_language_switch(key: str) -> None:
    """Render one mutually exclusive language choice, defaulting to Arabic."""

    language = normalize_ui_language(st.session_state.get("ui_language"))
    selected = st.segmented_control(
        _t("language"),
        ["ar", "en"],
        default=language,
        format_func=lambda value: _t(f"language_{value}"),
        selection_mode="single",
        required=True,
        key=key,
        label_visibility="collapsed",
        width="stretch",
    )
    if selected and selected != language:
        st.session_state.ui_language = selected
        st.rerun()


def _apply_ui_style() -> None:
    """Apply a restrained chat-workspace theme without external assets."""

    language = normalize_ui_language(st.session_state.get("ui_language"))
    direction = "rtl" if language == "ar" else "ltr"
    align = "right" if language == "ar" else "left"
    st.markdown(
        f"""
        <style>
        :root {{
            --raise-green: #2f6b45;
            --raise-border: #e3e7e2;
            --raise-muted: #667069;
            --raise-surface: #fbfcfa;
        }}
        [data-testid="stAppViewContainer"] {{ background: var(--raise-surface); }}
        [data-testid="stSidebar"] {{
            background: #f4f7f3;
            border-inline-end: 1px solid var(--raise-border);
        }}
        [data-testid="stSidebar"] > div:first-child {{ padding-top: 1rem; }}
        [data-testid="stMainBlockContainer"] {{
            max-width: 940px;
            padding-top: 1.25rem;
            padding-bottom: 7rem;
        }}
        [data-testid="stChatMessage"] {{
            background: transparent;
            border: 0;
            padding-block: .8rem;
        }}
        [data-testid="stChatMessageContent"] {{ unicode-bidi: plaintext; }}
        [data-testid="stChatInput"] {{
            background: #ffffff;
            border: 1px solid var(--raise-border);
            border-radius: 1.15rem;
            box-shadow: 0 8px 30px rgba(28, 50, 34, .08);
        }}
        [data-testid="stChatInput"]:focus-within {{
            border-color: #7aa387;
            box-shadow: 0 8px 30px rgba(47, 107, 69, .13);
        }}
        .stButton > button, .stDownloadButton > button {{
            border-radius: .75rem;
            min-height: 2.45rem;
        }}
        [data-testid="stExpander"], [data-testid="stPopover"] > button {{
            border-color: var(--raise-border);
            border-radius: .75rem;
        }}
        .raise-brand {{
            font-size: 1.25rem;
            font-weight: 750;
            letter-spacing: -.02em;
            margin: .15rem 0 0;
        }}
        .raise-muted {{ color: var(--raise-muted); font-size: .9rem; }}
        .raise-welcome {{ text-align: center; padding: 9vh 1rem 1.5rem; }}
        .raise-welcome h1 {{
            font-size: clamp(1.65rem, 4vw, 2.25rem);
            margin-bottom: .45rem;
        }}
        .raise-context {{
            color: var(--raise-muted);
            font-size: .88rem;
            margin-top: -.35rem;
        }}
        .raise-safety {{
            color: var(--raise-muted);
            font-size: .78rem;
            text-align: center;
            margin-top: .3rem;
        }}
        [data-testid="stSidebar"], [data-testid="stMainBlockContainer"] {{
            direction: {direction};
            text-align: {align};
        }}
        [data-testid="stChatMessageContent"], pre, code {{
            direction: initial;
            text-align: start;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _legal_url(document: str) -> str:
    base = APP_PUBLIC_URL or ""
    if not base:
        return f"?legal={document}"
    separator = "&" if "?" in base else "?"
    return f"{base}{separator}legal={document}"


def _render_public_legal(document: str) -> None:
    if document == "privacy":
        title = _t("privacy_policy")
        content = (
            privacy_policy_markdown_ar()
            if st.session_state.ui_language == "ar"
            else privacy_policy_markdown()
        )
    else:
        title = _t("user_agreement")
        content = (
            agreement_markdown_ar()
            if st.session_state.ui_language == "ar"
            else agreement_markdown()
        )
    st.subheader(title)
    st.markdown(content)


def render_login() -> None:
    st.markdown(
        f'<div class="raise-brand">🌿 {APP_DISPLAY_NAME}</div>',
        unsafe_allow_html=True,
    )
    _render_language_switch("login_language")
    legal_view = str(st.query_params.get("legal") or "").strip().lower()
    if legal_view in {"privacy", "terms"}:
        _render_public_legal(legal_view)
        st.markdown(f"[← {_t('back_to_app')}]({APP_PUBLIC_URL or './'})")
    else:
        st.title(_t("login_heading"))
        st.write(_t("login_body"))
        st.info(_t("login_safety"), icon="🛡️")
        st.markdown(
            f"[{_t('privacy_policy')}]({_legal_url('privacy')}) · "
            f"[{_t('user_agreement')}]({_legal_url('terms')})"
        )
    st.write(_t("login_note"))
    st.button(
        _t("continue_google"),
        type="primary",
        on_click=st.login,
        use_container_width=True,
    )


def public_identity() -> UserIdentity | None:
    """Resolve identity before initializing private workspace services."""

    try:
        identity = current_streamlit_identity(st)
    except IdentityError as exc:
        st.error(str(exc))
        if AUTH_MODE == "google":
            st.button(_t("logout"), on_click=st.logout)
        return None
    if identity is None:
        render_login()
    return identity


def ensure_identity(
    store: PilotStore,
    identity: UserIdentity | None = None,
) -> tuple[UserIdentity, dict[str, Any]] | None:
    if identity is None:
        identity = public_identity()
    if identity is None:
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
    st.title(_t("consent_title"))
    _render_language_switch("consent_language")
    st.warning(_t("consent_notice"))
    agreement = (
        agreement_markdown_ar()
        if st.session_state.ui_language == "ar"
        else agreement_markdown()
    )
    privacy = (
        privacy_policy_markdown_ar()
        if st.session_state.ui_language == "ar"
        else privacy_policy_markdown()
    )
    with st.expander(_t("read_agreement")):
        st.markdown(agreement)
    with st.expander(_t("read_privacy")):
        st.markdown(privacy)
    accepted_terms = st.checkbox(_t("consent_terms", version=CONSENT_VERSION))
    accepted_processing = st.checkbox(_t("consent_processing"))
    accepted_safety = st.checkbox(_t("consent_safety"))
    accepted_age = st.checkbox(_t("consent_age"))
    accepted = (
        accepted_terms and accepted_processing and accepted_safety and accepted_age
    )
    if st.button(_t("accept_continue"), type="primary", disabled=not accepted):
        store.accept_consent(identity.user_id)
        st.rerun()
    st.caption(_t("privacy_questions", email=PRIVACY_CONTACT_EMAIL))
    if AUTH_MODE == "google":
        st.button(_t("logout"), on_click=st.logout)
    st.stop()


def _delete_paths(storage: PrivateFileStorage, paths: list[str]) -> list[str]:
    failed: list[str] = []
    for path in paths:
        try:
            storage.delete(path)
        except Exception:  # noqa: BLE001 - continue deleting owned files
            failed.append(path)
    return failed


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


def render_data_controls(
    identity: UserIdentity,
    store: PilotStore,
    storage: PrivateFileStorage,
) -> None:
    """Render account data controls inside the settings dialog."""

    st.caption(
        _t(
            "agreement_version",
            version=CONSENT_VERSION,
            days=RETENTION_DAYS,
        )
    )
    st.caption(_t("privacy_questions", email=PRIVACY_CONTACT_EMAIL))
    with st.expander(_t("read_legal")):
        document = st.radio(
            _t("choose_document"),
            ["terms", "privacy"],
            format_func=lambda value: _t(
                "user_agreement" if value == "terms" else "privacy_policy"
            ),
            horizontal=True,
            key="settings_legal_document",
        )
        if st.session_state.ui_language == "ar":
            content = (
                agreement_markdown_ar()
                if document == "terms"
                else privacy_policy_markdown_ar()
            )
        else:
            content = (
                agreement_markdown()
                if document == "terms"
                else privacy_policy_markdown()
            )
        st.markdown(content)

    export_json = json.dumps(
        store.export_user_data(identity.user_id),
        ensure_ascii=False,
        indent=2,
        default=str,
    )
    st.download_button(
        _t("download_data"),
        data=export_json,
        file_name="raise-esdu-my-data.json",
        mime="application/json",
        key="download_account_data",
        use_container_width=True,
    )
    st.caption(_t("download_note"))
    required_phrase = _t("delete_account_phrase")
    confirmation = st.text_input(
        _t("delete_account_instruction"),
        key="account_delete_confirmation",
    )
    if st.button(
        _t("delete_account"),
        type="secondary",
        disabled=confirmation.strip() != required_phrase,
        key="delete_account_button",
        use_container_width=True,
    ):
        failed = _delete_paths(storage, store.user_storage_paths(identity.user_id))
        if failed:
            st.error(_t("delete_failed"))
            return
        store.delete_user_records(identity.user_id)
        if AUTH_MODE == "google":
            st.logout()
        st.session_state.clear()
        st.rerun()


def _initialize_preferences(user: dict[str, Any]) -> None:
    configured_mode = user.get("default_mode", "standard")
    if configured_mode not in MODE_PROFILES:
        configured_mode = "standard"
    if st.session_state.active_mode not in MODE_PROFILES:
        st.session_state.active_mode = configured_mode

    available_models = list(OPENROUTER_ALLOWED_MODELS)
    default_model = (
        OPENROUTER_DEFAULT_MODEL
        if OPENROUTER_DEFAULT_MODEL in available_models
        else available_models[0]
    )
    if st.session_state.active_model not in available_models:
        st.session_state.active_model = default_model
    if st.session_state.active_clarification_style not in CLARIFICATION_STYLES:
        st.session_state.active_clarification_style = "auto"


def _prepare_settings_drafts() -> None:
    st.session_state.settings_mode_draft = st.session_state.active_mode
    st.session_state.settings_model_draft = st.session_state.active_model
    st.session_state.settings_style_draft = st.session_state.active_clarification_style


def _render_settings_dialog_body(
    identity: UserIdentity,
    store: PilotStore,
    storage: PrivateFileStorage,
) -> None:
    answer_tab, privacy_tab = st.tabs([_t("answer_settings"), _t("privacy_data")])
    with answer_tab:
        mode_key = st.selectbox(
            _t("response_mode"),
            list(MODE_PROFILES),
            format_func=_mode_label,
            key="settings_mode_draft",
        )
        st.caption(_t(f"mode_{mode_key}_help"))
        model_id = st.selectbox(
            _t("ai_model"),
            list(OPENROUTER_ALLOWED_MODELS),
            format_func=_model_label,
            key="settings_model_draft",
        )
        st.caption(_t("model_help"))
        model_help_key = MODEL_DESCRIPTION_KEYS.get(model_id)
        if model_help_key:
            st.caption(_t(model_help_key))
        clarification_style = st.selectbox(
            _t("conversation_style"),
            list(CLARIFICATION_STYLES),
            format_func=_clarification_label,
            key="settings_style_draft",
        )
        st.caption(_t(f"style_{clarification_style}_help"))
        if st.button(
            _t("save_settings"),
            type="primary",
            key="save_answer_settings",
            use_container_width=True,
        ):
            st.session_state.active_mode = mode_key
            st.session_state.active_model = model_id
            st.session_state.active_clarification_style = clarification_style
            store.update_user_preferences(
                identity.user_id,
                default_mode=mode_key,
            )
            st.toast(_t("settings_saved"))
            st.rerun()
    with privacy_tab:
        render_data_controls(identity, store, storage)
        if identity.is_admin:
            with st.expander(_t("pilot_metrics")):
                st.json(
                    {
                        **store.performance_summary(),
                        **store.feedback_summary(),
                    }
                )


@st.dialog("الإعدادات", width="large")
def _settings_dialog_ar(
    identity: UserIdentity,
    store: PilotStore,
    storage: PrivateFileStorage,
) -> None:
    _render_settings_dialog_body(identity, store, storage)


@st.dialog("Settings", width="large")
def _settings_dialog_en(
    identity: UserIdentity,
    store: PilotStore,
    storage: PrivateFileStorage,
) -> None:
    _render_settings_dialog_body(identity, store, storage)


def _open_settings_dialog(
    identity: UserIdentity,
    store: PilotStore,
    storage: PrivateFileStorage,
) -> None:
    if st.session_state.ui_language == "ar":
        _settings_dialog_ar(identity, store, storage)
    else:
        _settings_dialog_en(identity, store, storage)


def _render_project_dialog_body(
    identity: UserIdentity,
    store: PilotStore,
    storage: PrivateFileStorage,
) -> None:
    create_tab, current_tab = st.tabs([_t("create_project"), _t("current_project")])
    with create_tab:
        with st.form("create_project_dialog_form", clear_on_submit=True):
            name = st.text_input(_t("project_name"))
            instructions = st.text_area(
                _t("project_instructions"),
                help=_t("project_instructions_help"),
            )
            if st.form_submit_button(
                _t("create"),
                type="primary",
                use_container_width=True,
            ):
                try:
                    project_id = store.create_project(
                        identity.user_id,
                        name,
                        instructions,
                    )
                    st.session_state.project_id = project_id
                    st.session_state.workspace_project_selector = project_id
                    st.session_state.conversation_id = None
                    st.rerun()
                except ValueError as exc:
                    st.warning(str(exc))

    with current_tab:
        selected = st.session_state.project_id
        if not selected:
            st.info(_t("no_project"))
            return
        project = store.get_project(identity.user_id, selected)
        with st.form(f"edit_project_dialog_{selected}"):
            name = st.text_input(_t("name"), value=project["name"])
            instructions = st.text_area(
                _t("instructions"),
                value=project["instructions"],
                help=_t("project_instructions_help"),
            )
            if st.form_submit_button(
                _t("save_project"),
                use_container_width=True,
            ):
                store.update_project(
                    identity.user_id,
                    selected,
                    name=name,
                    instructions=instructions,
                )
                st.toast(_t("project_saved"))
                st.rerun()

        st.markdown(f"#### {_t('reference_files')}")
        uploader = st.file_uploader(
            _t("upload_reference"),
            type=["pdf", "docx", "txt", "csv", "xlsx"],
            accept_multiple_files=True,
            key=f"project_dialog_upload_{selected}",
            help=_t("upload_reference_help"),
        )
        if uploader and st.button(
            _t("process_files"),
            key=f"project_dialog_process_{selected}",
            type="primary",
            use_container_width=True,
        ):
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
                st.toast(_t("processed_files", count=uploaded))
                st.rerun()

        documents = store.list_documents(identity.user_id, selected)
        if not documents:
            st.caption(_t("no_documents"))
        for document in documents:
            col_name, col_download, col_delete = st.columns([5, 1.4, 1.1])
            col_name.caption(
                f"📄 {document['filename']} · {document['size_bytes'] // 1024} KB"
            )
            signed_url = storage.signed_url(
                document["storage_path"],
                expires_seconds=600,
            )
            if signed_url:
                col_download.link_button(_t("download"), signed_url)
            else:
                try:
                    col_download.download_button(
                        _t("download"),
                        data=storage.get(document["storage_path"]),
                        file_name=document["filename"],
                        mime=document["mime_type"],
                        key=f"dialog_download_doc_{document['id']}",
                    )
                except (FileNotFoundError, RuntimeError):
                    col_download.caption(_t("unavailable"))
            if col_delete.button(
                _t("delete"),
                key=f"dialog_delete_doc_{document['id']}",
            ):
                DocumentService(store, storage).delete(
                    identity.user_id,
                    selected,
                    document["id"],
                )
                st.rerun()

        st.divider()
        confirmed = st.checkbox(
            _t("delete_project_confirm"),
            key=f"confirm_delete_project_{selected}",
        )
        if st.button(
            _t("delete_project"),
            key=f"dialog_delete_project_{selected}",
            disabled=not confirmed,
            use_container_width=True,
        ):
            failed = _delete_paths(
                storage,
                store.project_storage_paths(identity.user_id, selected),
            )
            if failed:
                st.error(_t("project_delete_failed"))
            else:
                store.delete_project(identity.user_id, selected)
                st.session_state.project_id = None
                st.session_state.workspace_project_selector = None
                st.session_state.conversation_id = None
                st.rerun()


@st.dialog("إدارة المشاريع", width="large")
def _project_dialog_ar(
    identity: UserIdentity,
    store: PilotStore,
    storage: PrivateFileStorage,
) -> None:
    _render_project_dialog_body(identity, store, storage)


@st.dialog("Manage projects", width="large")
def _project_dialog_en(
    identity: UserIdentity,
    store: PilotStore,
    storage: PrivateFileStorage,
) -> None:
    _render_project_dialog_body(identity, store, storage)


def _open_project_dialog(
    identity: UserIdentity,
    store: PilotStore,
    storage: PrivateFileStorage,
) -> None:
    if st.session_state.ui_language == "ar":
        _project_dialog_ar(identity, store, storage)
    else:
        _project_dialog_en(identity, store, storage)


def render_conversation_manager(
    identity: UserIdentity,
    store: PilotStore,
    project_id: str | None,
) -> str:
    search = st.text_input(
        _t("search_chats"),
        key="chat_search",
        placeholder=_t("search_chats"),
        label_visibility="collapsed",
        icon="🔎",
    )
    conversations = store.list_conversations(
        identity.user_id,
        project_id=project_id,
        search=search,
    )
    conversation_id = ensure_conversation(identity, store, project_id)
    st.caption(_t("recent_chats"))
    if search and not conversations:
        st.caption(_t("no_search_results"))
    for conversation in conversations[:30]:
        label = conversation["title"]
        if label == "New conversation":
            label = _t("new_conversation")
        if st.button(
            label,
            key=f"conversation_{conversation['id']}",
            type=("primary" if conversation["id"] == conversation_id else "secondary"),
            use_container_width=True,
        ):
            st.session_state.conversation_id = conversation["id"]
            st.rerun()
    return conversation_id


def render_sidebar(
    identity: UserIdentity,
    user: dict[str, Any],
    store: PilotStore,
    storage: PrivateFileStorage,
) -> tuple[str, str, str, str | None, str]:
    _initialize_preferences(user)
    with st.sidebar:
        st.markdown(
            f'<div class="raise-brand">🌿 {APP_DISPLAY_NAME}</div>',
            unsafe_allow_html=True,
        )
        st.caption(_t("tagline"))
        _render_language_switch("workspace_language")

        projects = store.list_projects(identity.user_id)
        project_options = [None, *[project["id"] for project in projects]]
        project_by_id = {project["id"]: project for project in projects}
        if st.session_state.project_id not in project_options:
            st.session_state.project_id = None
        if (
            "workspace_project_selector" not in st.session_state
            or st.session_state.workspace_project_selector not in project_options
        ):
            st.session_state.workspace_project_selector = st.session_state.project_id
        if st.button(
            f"＋ {_t('new_chat')}",
            key="new_chat_button",
            type="primary",
            use_container_width=True,
        ):
            st.session_state.conversation_id = store.create_conversation(
                identity.user_id,
                project_id=st.session_state.project_id,
            )
            st.rerun()

        def project_changed() -> None:
            st.session_state.project_id = st.session_state.workspace_project_selector
            st.session_state.conversation_id = None

        project_id = st.selectbox(
            _t("project"),
            project_options,
            format_func=lambda item: (
                _t("no_project") if item is None else project_by_id[item]["name"]
            ),
            key="workspace_project_selector",
            on_change=project_changed,
        )
        if st.button(
            f"📁 {_t('manage_projects')}",
            key="open_project_dialog",
            use_container_width=True,
        ):
            _open_project_dialog(identity, store, storage)

        st.divider()
        conversation_id = render_conversation_manager(
            identity,
            store,
            project_id,
        )
        st.divider()
        st.caption(f"{identity.name} · {identity.email or _t('whatsapp_identity')}")
        if identity.is_admin:
            st.caption(_t("pilot_admin"))
        st.caption(_t("queries_left", count=st.session_state.remaining_queries))
        if st.button(
            f"⚙️ {_t('settings')}",
            key="open_settings_dialog",
            use_container_width=True,
        ):
            _prepare_settings_drafts()
            _open_settings_dialog(identity, store, storage)
        if AUTH_MODE == "google":
            st.button(
                _t("logout"),
                key="sidebar_logout",
                on_click=st.logout,
                use_container_width=True,
            )
    return (
        st.session_state.active_mode,
        st.session_state.active_clarification_style,
        st.session_state.active_model,
        project_id,
        conversation_id,
    )


def render_chat_header(
    identity: UserIdentity,
    store: PilotStore,
    storage: PrivateFileStorage,
    project_id: str | None,
    conversation_id: str,
) -> None:
    conversation = store.get_conversation(identity.user_id, conversation_id)
    title = conversation["title"]
    if title == "New conversation":
        title = _t("new_conversation")
    heading, actions = st.columns([10, 1])
    heading.subheader(title)
    if project_id:
        project = store.get_project(identity.user_id, project_id)
        heading.caption(_t("project_context", name=project["name"]))
    else:
        heading.caption(_t("standalone_chat"))

    with actions.popover("•••", use_container_width=True):
        st.caption(_t("chat_options"))
        with st.form(f"rename_chat_{conversation_id}"):
            renamed = st.text_input(_t("chat_title"), value=conversation["title"])
            if st.form_submit_button(
                _t("rename"),
                use_container_width=True,
            ):
                store.rename_conversation(
                    identity.user_id,
                    conversation_id,
                    renamed,
                )
                st.rerun()
        if st.button(
            _t("archive_chat"),
            key=f"archive_chat_{conversation_id}",
            use_container_width=True,
        ):
            store.archive_conversation(identity.user_id, conversation_id)
            st.session_state.conversation_id = None
            st.rerun()
        confirmed = st.checkbox(
            _t("delete_chat_confirm"),
            key=f"confirm_delete_chat_{conversation_id}",
        )
        if st.button(
            _t("delete_chat"),
            key=f"delete_chat_{conversation_id}",
            disabled=not confirmed,
            use_container_width=True,
        ):
            failed = _delete_paths(
                storage,
                store.conversation_storage_paths(
                    identity.user_id,
                    conversation_id,
                ),
            )
            if failed:
                st.error(_t("chat_delete_failed"))
            else:
                store.delete_conversation(identity.user_id, conversation_id)
                st.session_state.conversation_id = None
                st.rerun()


def render_citations(citations: list[dict[str, Any]]) -> None:
    if not citations:
        return
    with st.expander(f"📚 {_t('sources', count=len(citations))}"):
        for citation in citations:
            source_type = citation.get("source_type")
            if source_type == "raise_knowledge":
                st.markdown(
                    f"**[{citation.get('item_id')}] {citation.get('title')}**  \n"
                    + _t(
                        "source_status",
                        status=f"`{citation.get('status')}`",
                        evidence=f"`{citation.get('evidence_class')}`",
                    )
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
                    f"**{_t('user_document', title=citation.get('title'))}**  \n"
                    f"_{_t('user_document_notice')}_"
                )
            elif source_type == "trusted_live":
                url = citation.get("url")
                title = citation.get("title") or citation.get("domain") or url
                if url:
                    st.markdown(f"**{_t('trusted_source')}:** [{title}]({url})")
                else:
                    st.write(title)
            else:
                url = citation.get("url")
                title = citation.get("title") or citation.get("domain") or url
                if url:
                    st.markdown(f"**{_t('model_source')}:** [{title}]({url})")
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
                    _t("download_artifact", filename=artifact["filename"]),
                    signed_url,
                    use_container_width=True,
                )
                continue
            data = storage.get(artifact["storage_path"])
        except (ValueError, FileNotFoundError, RuntimeError):
            st.warning(_t("artifact_unavailable"))
            continue
        st.download_button(
            _t("download_artifact", filename=artifact["filename"]),
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
    if columns[0].button(
        "👍",
        key=f"helpful_{message['id']}",
        help=_t("helpful"),
    ):
        store.record_feedback(
            user_id=identity.user_id,
            message_id=message["id"],
            category="helpful",
            comment="Helpful answer",
            consent=True,
            rating=5,
            language=message.get("language"),
        )
        st.toast(_t("feedback_saved"))
    if columns[1].button(
        "👎",
        key=f"not_helpful_{message['id']}",
        help=_t("not_helpful"),
    ):
        store.record_feedback(
            user_id=identity.user_id,
            message_id=message["id"],
            category="not_helpful",
            comment="Answer needs improvement",
            consent=True,
            rating=1,
            language=message.get("language"),
        )
        st.toast(_t("feedback_saved"))
    with st.popover(f"📋 {_t('copy_answer')}"):
        st.code(message["content"], language=None)


def render_audio(message: dict[str, Any]) -> None:
    if not EDGE_TTS_AVAILABLE:
        return
    with st.popover(f"🔊 {_t('voice')}"):
        st.caption(_t("voice_notice"))
        if st.button(_t("generate_audio"), key=f"audio_{message['id']}"):
            try:
                st.audio(
                    synthesize_edge(
                        message["content"],
                        message.get("language") or detect_language(message["content"]),
                    )
                )
            except Exception:  # noqa: BLE001 - optional provider boundary
                st.warning(_t("audio_failed"))


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
                        st.caption(_t("attached_unavailable"))
            if message.get("warning"):
                st.warning(message["warning"])
            st.markdown(message["content"])
            if message["role"] == "assistant":
                render_citations(message.get("citations") or [])
                if message.get("tools"):
                    st.caption(_t("tools_used", tools=", ".join(message["tools"])))
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
        raise ValueError(_t("image_invalid_size"))
    if upload.type not in {"image/jpeg", "image/png"}:
        raise ValueError(_t("image_invalid_type"))
    try:
        with Image.open(io.BytesIO(data)) as uploaded_image:
            uploaded_image.load()
            if uploaded_image.width * uploaded_image.height > 24_000_000:
                raise ValueError(_t("image_dimensions"))
            image = ImageOps.exif_transpose(uploaded_image)
            image.thumbnail((2048, 2048), Image.Resampling.LANCZOS)
            normalized = io.BytesIO()
            if upload.type == "image/png":
                mode = "RGBA" if "A" in image.getbands() else "RGB"
                image.convert(mode).save(normalized, format="PNG", optimize=True)
            else:
                image.convert("RGB").save(
                    normalized,
                    format="JPEG",
                    quality=90,
                    optimize=True,
                )
            data = normalized.getvalue()
    except Exception as exc:
        if isinstance(exc, ValueError):
            raise
        raise ValueError(_t("image_invalid")) from exc
    if not data or len(data) > MAX_CHAT_IMAGE_BYTES:
        raise ValueError(_t("image_normalized_size"))
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
        page_title=APP_DISPLAY_NAME,
        page_icon="🌿",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _init_state()
    _apply_ui_style()
    validate_web_runtime()
    identity = public_identity()
    if identity is None:
        return
    knowledge, store, storage, trusted_client = get_services()
    identity_result = ensure_identity(store, identity)
    if not identity_result:
        return
    identity, user = identity_result
    render_consent(identity, store)
    (
        mode_key,
        clarification_style,
        model_id,
        project_id,
        conversation_id,
    ) = render_sidebar(
        identity,
        user,
        store,
        storage,
    )
    render_chat_header(
        identity,
        store,
        storage,
        project_id,
        conversation_id,
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
        if previous_user and st.button(
            f"↻ {_t('regenerate')}",
            key="regenerate_last_answer",
        ):
            st.session_state.pending_prompt = previous_user
            st.rerun()

    model_supports_images = MODEL_CATALOG[model_id].supports_images
    submission = st.chat_input(
        _t("composer_placeholder"),
        key=f"chat_composer_{st.session_state.image_uploader_version}",
        accept_file=model_supports_images,
        file_type=["jpg", "jpeg", "png"] if model_supports_images else None,
        max_upload_size=5 if model_supports_images else None,
    )
    chat_image = None
    user_input = ""
    if isinstance(submission, str):
        user_input = submission
    elif submission is not None:
        user_input = submission.text or ""
        files = list(submission.files or [])
        chat_image = files[0] if files else None
    st.markdown(
        f'<div class="raise-safety">{_t("safety_short")}</div>',
        unsafe_allow_html=True,
    )
    if model_supports_images:
        st.caption(_t("composer_image_note"))
    else:
        st.caption(_t("composer_no_image"))
    if chat_image and not user_input.strip():
        user_input = _t("image_only_prompt")
    if st.session_state.pending_prompt:
        user_input = st.session_state.pending_prompt
        st.session_state.pending_prompt = None

    if not user_input:
        if not messages:
            st.markdown(
                f"""
                <div class="raise-welcome">
                    <h1>🌿 {_t("welcome_title")}</h1>
                    <div class="raise-muted">{_t("welcome_body")}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.caption(_t("try_question"))
            suggestions = [_t(f"suggestion_{index}") for index in range(1, 5)]
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
        model_id=model_id,
        clarification_style=clarification_style,
        project_instructions=project_instructions,
    )
    with st.spinner(_t("checking")):
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
