"""Application configuration and capability profiles."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _csv_set(name: str) -> frozenset[str]:
    return frozenset(
        value.strip().lower()
        for value in os.getenv(name, "").split(",")
        if value.strip()
    )


@dataclass(frozen=True)
class ModeProfile:
    key: str
    label_en: str
    label_ar: str
    description: str
    model: str
    top_k: int
    max_tokens: int
    temperature: float
    reasoning_effort: str
    allow_general_knowledge: bool
    max_tool_rounds: int


DEFAULT_FAST_MODEL = os.getenv(
    "OPENROUTER_FAST_MODEL", "google/gemini-2.5-flash-lite"
)
DEFAULT_DEEP_MODEL = os.getenv(
    "OPENROUTER_DEEP_MODEL", "openai/gpt-5.4-mini"
)


MODE_PROFILES: dict[str, ModeProfile] = {
    "quick": ModeProfile(
        key="quick",
        label_en="Quick",
        label_ar="سريع",
        description="Short answer for routine questions and slower connections.",
        model=DEFAULT_FAST_MODEL,
        top_k=4,
        max_tokens=400,
        temperature=0.2,
        reasoning_effort="low",
        allow_general_knowledge=True,
        max_tool_rounds=1,
    ),
    "standard": ModeProfile(
        key="standard",
        label_en="Standard",
        label_ar="متوازن",
        description="Default balance of local evidence, detail, latency, and cost.",
        model=DEFAULT_FAST_MODEL,
        top_k=6,
        max_tokens=650,
        temperature=0.25,
        reasoning_effort="medium",
        allow_general_knowledge=True,
        max_tool_rounds=2,
    ),
    "deep": ModeProfile(
        key="deep",
        label_en="Deep",
        label_ar="متعمّق",
        description="More retrieval and reasoning for planning or comparison.",
        model=DEFAULT_DEEP_MODEL,
        top_k=9,
        max_tokens=1000,
        temperature=0.2,
        reasoning_effort="high",
        allow_general_knowledge=True,
        max_tool_rounds=3,
    ),
    "source_only": ModeProfile(
        key="source_only",
        label_en="Source only",
        label_ar="من المصادر فقط",
        description="Auditable answer restricted to the reviewed knowledge base.",
        model=DEFAULT_FAST_MODEL,
        top_k=10,
        max_tokens=650,
        temperature=0.0,
        reasoning_effort="low",
        allow_general_knowledge=False,
        max_tool_rounds=1,
    ),
}


OPENROUTER_API_URL = os.getenv(
    "OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions"
)
APP_ENV = os.getenv("APP_ENV", "development").lower()
APP_PUBLIC_URL = os.getenv("APP_PUBLIC_URL", "").rstrip("/")
AUTH_MODE = os.getenv("AUTH_MODE", "disabled").lower()
ACCESS_POLICY = os.getenv("ACCESS_POLICY", "google_any").lower()
ALLOWED_EMAILS = _csv_set("ALLOWED_EMAILS")
ALLOWED_DOMAINS = _csv_set("ALLOWED_DOMAINS")
ADMIN_EMAILS = _csv_set("ADMIN_EMAILS")
AGREEMENT_TEXT_VERSION = "pilot-2026-08-v1"
CONSENT_VERSION = os.getenv("CONSENT_VERSION", AGREEMENT_TEXT_VERSION)
ORGANIZATION_NAME = os.getenv(
    "ORGANIZATION_NAME", "RAISE / ESDU internal pilot"
).strip()
PRIVACY_CONTACT_EMAIL = os.getenv(
    "PRIVACY_CONTACT_EMAIL",
    "privacy-contact-not-configured@example.invalid",
).strip()
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
LOCAL_PILOT_DB_PATH = Path(os.getenv("LOCAL_PILOT_DB_PATH", "data/pilot.sqlite3"))
LOCAL_FILE_ROOT = Path(os.getenv("LOCAL_FILE_ROOT", "data/pilot_files"))
SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_STORAGE_BUCKET = os.getenv("SUPABASE_STORAGE_BUCKET", "pilot-files")
RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "30"))

MAX_QUERIES_PER_SESSION = int(os.getenv("MAX_QUERIES_PER_SESSION", "25"))
MAX_QUERIES_PER_DAY_GLOBAL = int(os.getenv("MAX_QUERIES_PER_DAY_GLOBAL", "300"))
COOLDOWN_SECONDS = float(os.getenv("COOLDOWN_SECONDS", "3"))
RUNTIME_DB_PATH = os.getenv("RUNTIME_DB_PATH", "data/runtime.sqlite3")

MAX_QUERIES_PER_USER_DAY = int(os.getenv("MAX_QUERIES_PER_USER_DAY", "30"))
MAX_PILOT_QUERIES_PER_DAY = int(os.getenv("MAX_PILOT_QUERIES_PER_DAY", "500"))
MAX_DEEP_QUERIES_PER_USER_DAY = int(
    os.getenv("MAX_DEEP_QUERIES_PER_USER_DAY", "10")
)
MAX_ARTIFACTS_PER_USER_DAY = int(os.getenv("MAX_ARTIFACTS_PER_USER_DAY", "10"))
PILOT_COOLDOWN_SECONDS = float(os.getenv("PILOT_COOLDOWN_SECONDS", "2"))
MAX_PROJECT_FILES = int(os.getenv("MAX_PROJECT_FILES", "5"))
MAX_PROJECT_FILE_BYTES = int(os.getenv("MAX_PROJECT_FILE_BYTES", str(10 * 1024 * 1024)))
MAX_CHAT_IMAGE_BYTES = int(os.getenv("MAX_CHAT_IMAGE_BYTES", str(5 * 1024 * 1024)))

ENABLE_TRUSTED_WEB_SEARCH = (
    os.getenv("ENABLE_TRUSTED_WEB_SEARCH", "false").lower() == "true"
)
TRUSTED_SEARCH_MODEL = os.getenv(
    "TRUSTED_SEARCH_MODEL",
    DEFAULT_FAST_MODEL,
)
TRUSTED_SEARCH_MAX_RESULTS = int(os.getenv("TRUSTED_SEARCH_MAX_RESULTS", "5"))
TRUSTED_SEARCH_MAX_CALLS = int(os.getenv("TRUSTED_SEARCH_MAX_CALLS", "2"))

META_APP_SECRET = os.getenv("META_APP_SECRET", "")
META_VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN", "")
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN", "")
META_PHONE_NUMBER_ID = os.getenv("META_PHONE_NUMBER_ID", "")
META_GRAPH_API_VERSION = os.getenv("META_GRAPH_API_VERSION", "v23.0")
WHATSAPP_ID_SECRET = os.getenv("WHATSAPP_ID_SECRET", "")
WHATSAPP_MAX_REPLY_CHARS = int(os.getenv("WHATSAPP_MAX_REPLY_CHARS", "3500"))
