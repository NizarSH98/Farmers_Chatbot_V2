"""Server-controlled trusted-source registry and bounded live search."""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse

import requests

from .config import (
    ENABLE_TRUSTED_WEB_SEARCH,
    TRUSTED_SEARCH_MAX_RESULTS,
)

LIVE_SOURCE_REGISTRY_VERSION = "raise-live-sources-v1"
DEFAULT_LIVE_SOURCE_REGISTRY = (
    Path(__file__).resolve().parents[1] / "config" / "live_sources.v1.json"
)
MAX_LIVE_SOURCE_BYTES = 1_000_000
ALLOWED_LIVE_CONTENT_TYPES = frozenset(
    {
        "application/json",
        "application/rss+xml",
        "application/xml",
        "text/html",
        "text/plain",
        "text/xml",
    }
)

TRUSTED_SOURCE_GROUPS: dict[str, tuple[str, ...]] = {
    "local": (
        "aub.edu.lb",
        "agriculture.gov.lb",
        "lari.gov.lb",
    ),
    "science": (
        "fao.org",
        "agris.fao.org",
        "icarda.org",
        "cgiar.org",
        "pubmed.ncbi.nlm.nih.gov",
        "who.int",
        "aub.edu.lb",
        "lari.gov.lb",
    ),
    "economic": (
        "agriculture.gov.lb",
        "fao.org",
        "faostat.org",
        "worldbank.org",
        "data.worldbank.org",
        "wfp.org",
        "ipcinfo.org",
        "undp.org",
    ),
}
ALL_TRUSTED_DOMAINS = tuple(
    sorted({domain for domains in TRUSTED_SOURCE_GROUPS.values() for domain in domains})
)

SupportStatus = Literal["supported", "unsupported", "unassessed"]
_SUPPORT_STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "was",
    "were",
    "with",
    "إلى",
    "أن",
    "او",
    "أو",
    "في",
    "من",
    "على",
    "عن",
}
_NEGATION_TOKENS = {"no", "not", "never", "without", "لا", "ليس", "غير", "بدون"}

DYNAMIC_OR_HIGH_RISK_PATTERNS = (
    (
        r"\b(today|now|current|latest|price|market|forecast|weather|alert|law|"
        r"regulation|registered|banned|pesticide|dose|veterinary|disease outbreak|"
        r"profit|cost|export|scientific evidence|research|study)\b"
    ),
    (
        r"(اليوم|حالياً|حاليًا|الأحدث|آخر|سعر|أسعار|السوق|الطقس|توقعات|"
        r"تنبيه|قانون|مبيد|جرعة|بيطري|مرض|ربح|كلفة|تصدير|بحث|دراسة)"
    ),
)


def _normalized_tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[\w\u0600-\u06ff]+", value.lower())
        if len(token) > 1 and token not in _SUPPORT_STOP_WORDS
    }


def assess_claim_support(claim: str, passage: str) -> SupportStatus:
    """Conservatively assess whether a cited passage supports one claim.

    This is deliberately lexical and fail-closed. It establishes support only
    when the cited claim and passage materially overlap; it is not presented as
    a semantic-entailment model.
    """

    normalized_claim = " ".join(claim.lower().split())
    normalized_passage = " ".join(passage.lower().split())
    if not normalized_claim or not normalized_passage:
        return "unassessed"
    claim_tokens = _normalized_tokens(normalized_claim)
    passage_tokens = _normalized_tokens(normalized_passage)
    if not claim_tokens or not passage_tokens:
        return "unassessed"
    claim_negation = bool(claim_tokens & _NEGATION_TOKENS)
    passage_negation = bool(passage_tokens & _NEGATION_TOKENS)
    if claim_negation != passage_negation:
        return "unsupported"
    claim_numbers = set(re.findall(r"\d+(?:[.,]\d+)?", normalized_claim))
    passage_numbers = set(re.findall(r"\d+(?:[.,]\d+)?", normalized_passage))
    if claim_numbers and not claim_numbers.issubset(passage_numbers):
        return "unsupported"
    if normalized_claim in normalized_passage:
        return "supported"
    overlap = claim_tokens & passage_tokens
    coverage = len(overlap) / len(claim_tokens)
    if coverage >= 0.9 and len(overlap) >= 3:
        return "supported"
    if coverage <= 0.25:
        return "unsupported"
    return "unassessed"


def _parse_timestamp(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def live_evidence_is_stale(
    expires_at: str,
    *,
    now: datetime | None = None,
) -> bool:
    expiry = _parse_timestamp(expires_at)
    if expiry is None:
        return True
    current = (now or datetime.now(UTC)).astimezone(UTC)
    return current >= expiry


@dataclass(frozen=True)
class LiveEvidence:
    evidence_id: str
    publisher: str
    title: str
    url: str
    passage: str
    claim: str
    observed_at: str
    expires_at: str
    category: str
    support_status: SupportStatus
    live_only: bool = True
    source_type: str = "trusted_live"

    @property
    def stale(self) -> bool:
        return live_evidence_is_stale(self.expires_at)

    @property
    def usable(self) -> bool:
        return self.support_status == "supported" and not self.stale

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "publisher": self.publisher,
            "title": self.title,
            "url": self.url,
            "passage": self.passage,
            "claim": self.claim,
            "observed_at": self.observed_at,
            "expires_at": self.expires_at,
            "category": self.category,
            "support_status": self.support_status,
            "live_only": self.live_only,
            "stale": self.stale,
            "source_type": self.source_type,
        }

    def to_citation(self) -> dict[str, Any]:
        return {
            **self.to_dict(),
            "domain": urlparse(self.url).hostname,
            "content": self.passage,
            "accessed_at": self.observed_at,
        }


@dataclass(frozen=True)
class TrustedSearchResult:
    available: bool
    verified: bool
    query: str
    category: str
    summary: str
    citations: tuple[dict[str, Any], ...]
    searched_at: str
    search_requests: int = 0
    warning: str | None = None
    evidence: tuple[LiveEvidence, ...] = ()
    support_status: SupportStatus = "unassessed"
    live_only: bool = True
    expires_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "available": self.available,
            "verified": self.verified,
            "query": self.query,
            "category": self.category,
            "summary": self.summary,
            "citations": list(self.citations),
            "searched_at": self.searched_at,
            "search_requests": self.search_requests,
            "warning": self.warning,
            "evidence": [item.to_dict() for item in self.evidence],
            "support_status": self.support_status,
            "live_only": self.live_only,
            "expires_at": self.expires_at,
        }


def host_is_trusted(
    host: str, allowed_domains: tuple[str, ...] = ALL_TRUSTED_DOMAINS
) -> bool:
    normalized = host.lower().strip(".")
    return any(
        normalized == domain or normalized.endswith(f".{domain}")
        for domain in allowed_domains
    )


def url_is_trusted(
    url: str, allowed_domains: tuple[str, ...] = ALL_TRUSTED_DOMAINS
) -> bool:
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    return (
        parsed.scheme == "https"
        and bool(parsed.hostname)
        and host_is_trusted(
            parsed.hostname or "",
            allowed_domains,
        )
    )


def classify_source_group(query: str) -> str:
    normalized = query.lower()
    if re.search(
        r"\b(price|market|cost|profit|budget|income|export|economic|economy|"
        r"business|break-even)\b|"
        r"(سعر|أسعار|سوق|كلفة|ربح|ميزانية|دخل|تصدير|اقتصاد)",
        normalized,
    ):
        return "economic"
    if re.search(
        r"\b(science|scientific|research|study|evidence|trial|biology|chemistry|"
        r"soil|disease|nutrition)\b|"
        r"(علم|علمي|بحث|دراسة|دليل|تجربة|تربة|مرض|تغذية)",
        normalized,
    ):
        return "science"
    return "local"


def requires_live_verification(query: str) -> bool:
    return any(
        re.search(pattern, query, flags=re.IGNORECASE)
        for pattern in DYNAMIC_OR_HIGH_RISK_PATTERNS
    )


@dataclass(frozen=True)
class LiveSourceDefinition:
    """One exact, operator-authorized source endpoint."""

    source_id: str
    publisher: str
    title: str
    url: str
    categories: tuple[str, ...]
    ttl_seconds: int
    authorized: bool = False
    keywords: tuple[str, ...] = ()
    allowed_content_types: tuple[str, ...] = tuple(ALLOWED_LIVE_CONTENT_TYPES)
    max_bytes: int = MAX_LIVE_SOURCE_BYTES


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[str] = []
        self._hidden_depth = 0

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        del attrs
        if tag.lower() in {"script", "style", "noscript", "svg"}:
            self._hidden_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript", "svg"}:
            self._hidden_depth = max(0, self._hidden_depth - 1)

    def handle_data(self, data: str) -> None:
        cleaned = " ".join(data.split())
        if not self._hidden_depth and cleaned:
            self.blocks.append(cleaned)


def _definition_from_dict(value: dict[str, Any]) -> LiveSourceDefinition:
    definition = LiveSourceDefinition(
        source_id=str(value.get("source_id") or "").strip(),
        publisher=str(value.get("publisher") or "").strip(),
        title=str(value.get("title") or "").strip(),
        url=str(value.get("url") or "").strip(),
        categories=tuple(str(item).strip() for item in value.get("categories") or ()),
        ttl_seconds=int(value.get("ttl_seconds") or 0),
        authorized=bool(value.get("authorized", False)),
        keywords=tuple(str(item).strip() for item in value.get("keywords") or ()),
        allowed_content_types=tuple(
            str(item).lower().strip()
            for item in value.get("allowed_content_types")
            or sorted(ALLOWED_LIVE_CONTENT_TYPES)
        ),
        max_bytes=int(value.get("max_bytes") or MAX_LIVE_SOURCE_BYTES),
    )
    _validate_definition(definition)
    return definition


def _validate_definition(definition: LiveSourceDefinition) -> None:
    if not definition.source_id or not definition.publisher or not definition.title:
        raise ValueError("Live source ID, publisher, and title are required")
    if not definition.categories or not set(definition.categories).issubset(
        TRUSTED_SOURCE_GROUPS
    ):
        raise ValueError("Live source categories must use the trusted registry")
    parsed = urlparse(definition.url)
    if (
        not url_is_trusted(definition.url)
        or parsed.username
        or parsed.password
        or parsed.fragment
        or "{" in definition.url
        or "}" in definition.url
    ):
        raise ValueError("Live source URL must be an exact trusted HTTPS endpoint")
    if not 60 <= definition.ttl_seconds <= 2_592_000:
        raise ValueError("Live source TTL must be between 60 seconds and 30 days")
    if not 1_024 <= definition.max_bytes <= MAX_LIVE_SOURCE_BYTES:
        raise ValueError("Live source response limit is outside the safe range")
    if not definition.allowed_content_types or not set(
        definition.allowed_content_types
    ).issubset(ALLOWED_LIVE_CONTENT_TYPES):
        raise ValueError("Live source content type is not supported")


def load_live_source_registry(
    path: str | Path | None = None,
) -> tuple[LiveSourceDefinition, ...]:
    registry_path = Path(
        path
        or os.getenv("LIVE_SOURCE_REGISTRY_PATH")
        or DEFAULT_LIVE_SOURCE_REGISTRY
    )
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    if data.get("schema_version") != LIVE_SOURCE_REGISTRY_VERSION:
        raise ValueError("Unsupported live source registry version")
    definitions = tuple(
        _definition_from_dict(item) for item in data.get("sources") or ()
    )
    source_ids = [item.source_id for item in definitions]
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("Duplicate live source IDs")
    return definitions


def validate_live_source_registry(
    path: str | Path | None = None,
    *,
    require_authorized: bool = False,
) -> tuple[LiveSourceDefinition, ...]:
    try:
        definitions = load_live_source_registry(path)
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Invalid live source registry: {exc}") from exc
    authorized = tuple(item for item in definitions if item.authorized)
    if require_authorized and not authorized:
        raise RuntimeError("Live search is enabled but no source is authorized")
    return authorized


def _decode_source_body(content_type: str, payload: bytes) -> str:
    decoded = payload.decode("utf-8", errors="replace")
    if content_type == "application/json":
        try:
            value = json.loads(decoded)
        except json.JSONDecodeError:
            return ""
        strings: list[str] = []

        def visit(item: Any) -> None:
            if isinstance(item, str):
                cleaned = " ".join(item.split())
                if cleaned:
                    strings.append(cleaned)
            elif isinstance(item, list):
                for child in item[:500]:
                    visit(child)
            elif isinstance(item, dict):
                for child in list(item.values())[:500]:
                    visit(child)

        visit(value)
        return "\n".join(strings)
    if content_type in {"text/html", "application/rss+xml", "application/xml", "text/xml"}:
        parser = _VisibleTextParser()
        try:
            parser.feed(decoded)
        except (ValueError, AssertionError):
            return ""
        return "\n".join(parser.blocks)
    return decoded


def _candidate_passages(text: str) -> tuple[str, ...]:
    blocks = [" ".join(item.split()) for item in text.splitlines()]
    blocks = [item for item in blocks if 40 <= len(item) <= 4000]
    if not blocks:
        compact = " ".join(text.split())
        blocks = [compact[index : index + 1800] for index in range(0, len(compact), 1800)]
    return tuple(blocks[:1000])


def _select_passage(
    query: str,
    definition: LiveSourceDefinition,
    text: str,
) -> str:
    query_tokens = _normalized_tokens(
        " ".join((query, definition.title, *definition.keywords))
    )
    ranked: list[tuple[float, int, str]] = []
    for index, passage in enumerate(_candidate_passages(text)):
        passage_tokens = _normalized_tokens(passage)
        overlap = query_tokens & passage_tokens
        if not overlap:
            continue
        coverage = len(overlap) / max(1, len(_normalized_tokens(query)))
        ranked.append((coverage + len(overlap) / 100, -index, passage))
    if not ranked:
        return ""
    return max(ranked)[2][:4000]


def _evidence_from_passage(
    definition: LiveSourceDefinition,
    passage: str,
    category: str,
    observed_at: str,
) -> LiveEvidence:
    expires_at = (
        datetime.fromisoformat(observed_at)
        + timedelta(seconds=definition.ttl_seconds)
    ).isoformat()
    identity = f"{definition.source_id}\n{definition.url}\n{passage}\n{observed_at}"
    return LiveEvidence(
        evidence_id=(
            f"live_{hashlib.sha256(identity.encode('utf-8')).hexdigest()[:24]}"
        ),
        publisher=definition.publisher[:200],
        title=definition.title[:300],
        url=definition.url,
        passage=passage,
        claim=passage,
        observed_at=observed_at,
        expires_at=expires_at,
        category=category,
        support_status="supported",
        source_type="trusted_live",
    )


class TrustedSourceClient:
    def __init__(
        self,
        api_key: str | None,
        *,
        enabled: bool = ENABLE_TRUSTED_WEB_SEARCH,
        model: str | None = None,
        timeout_seconds: float = 35,
        definitions: tuple[LiveSourceDefinition, ...] | None = None,
        registry_path: str | Path | None = None,
        session: requests.Session | None = None,
    ) -> None:
        # api_key/model remain accepted for the one-release public constructor;
        # direct source connectors never receive provider credentials.
        self.api_key = api_key
        self.enabled = bool(enabled)
        self.model = model
        self.timeout_seconds = max(1.0, min(float(timeout_seconds), 35.0))
        self.session = session or requests.Session()
        self.registry_error: str | None = None
        if definitions is not None:
            for definition in definitions:
                _validate_definition(definition)
            self.definitions = tuple(item for item in definitions if item.authorized)
        elif self.enabled:
            try:
                self.definitions = validate_live_source_registry(registry_path)
            except RuntimeError as exc:
                self.definitions = ()
                self.registry_error = str(exc)
        else:
            self.definitions = ()

    def search(self, query: str, category: str = "auto") -> TrustedSearchResult:
        searched_at = datetime.now(UTC).isoformat()
        category = classify_source_group(query) if category == "auto" else category
        if category not in TRUSTED_SOURCE_GROUPS:
            raise ValueError(
                "Trusted source category must be local, science, or economic"
            )
        if not self.enabled or not self.definitions:
            return TrustedSearchResult(
                available=False,
                verified=False,
                query=query,
                category=category,
                summary="",
                citations=(),
                searched_at=searched_at,
                warning=(
                    self.registry_error
                    or "Trusted live search has no authorized source connector."
                ),
            )
        candidates = [
            item for item in self.definitions if category in item.categories
        ][: max(1, min(TRUSTED_SEARCH_MAX_RESULTS, 5))]
        evidence: list[LiveEvidence] = []
        attempts = 0
        for definition in candidates:
            attempts += 1
            try:
                response = self.session.get(
                    definition.url,
                    headers={
                        "Accept": ", ".join(definition.allowed_content_types),
                        "User-Agent": "RAISE-Live-Evidence/1.0",
                    },
                    timeout=(min(5.0, self.timeout_seconds), self.timeout_seconds),
                    allow_redirects=False,
                    stream=True,
                )
                if response.status_code != 200:
                    continue
                content_type = str(response.headers.get("Content-Type") or "").split(
                    ";", 1
                )[0].lower().strip()
                if content_type not in definition.allowed_content_types:
                    continue
                raw_length = response.headers.get("Content-Length")
                if raw_length and int(raw_length) > definition.max_bytes:
                    continue
                payload = bytearray()
                oversized = False
                for chunk in response.iter_content(chunk_size=65_536):
                    if not chunk:
                        continue
                    payload.extend(chunk)
                    if len(payload) > definition.max_bytes:
                        oversized = True
                        break
                if oversized:
                    continue
                passage = _select_passage(
                    query,
                    definition,
                    _decode_source_body(content_type, bytes(payload)),
                )
                if passage:
                    evidence.append(
                        _evidence_from_passage(
                            definition,
                            passage,
                            category,
                            searched_at,
                        )
                    )
            except (requests.RequestException, TypeError, ValueError, OSError):
                continue

        usable_evidence = [item for item in evidence if item.usable]
        citations = tuple(item.to_citation() for item in usable_evidence)
        summary = "\n\n".join(item.passage for item in usable_evidence)[:12000]
        expires_at = min(
            (item.expires_at for item in usable_evidence),
            default=None,
        )
        return TrustedSearchResult(
            available=bool(candidates),
            verified=bool(usable_evidence),
            query=query,
            category=category,
            summary=summary,
            citations=citations,
            searched_at=searched_at,
            search_requests=attempts,
            warning=(
                None
                if usable_evidence
                else "Authorized sources returned no relevant supported passage."
            ),
            evidence=tuple(evidence),
            support_status="supported" if usable_evidence else "unassessed",
            expires_at=expires_at,
        )

    @staticmethod
    def verify_url(url: str) -> dict[str, Any]:
        parsed = urlparse(url)
        return {
            "url": url,
            "trusted": url_is_trusted(url),
            "domain": parsed.hostname,
            "support_status": "unassessed",
            "warning": "Domain trust does not verify support for a claim.",
            "registry_version": LIVE_SOURCE_REGISTRY_VERSION,
        }
