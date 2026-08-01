"""Server-controlled trusted-source registry and bounded live search."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse

import requests

from .config import (
    ENABLE_TRUSTED_WEB_SEARCH,
    OPENROUTER_API_URL,
    OPENROUTER_DATA_COLLECTION,
    OPENROUTER_ENFORCE_ZDR,
    TRUSTED_SEARCH_MAX_CALLS,
    TRUSTED_SEARCH_MAX_RESULTS,
    TRUSTED_SEARCH_MODEL,
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


class TrustedSourceClient:
    def __init__(
        self,
        api_key: str | None,
        *,
        enabled: bool = ENABLE_TRUSTED_WEB_SEARCH,
        model: str = TRUSTED_SEARCH_MODEL,
        timeout_seconds: float = 35,
    ) -> None:
        self.api_key = api_key
        self.enabled = bool(enabled and api_key)
        self.model = model
        self.timeout_seconds = timeout_seconds

    def search(self, query: str, category: str = "auto") -> TrustedSearchResult:
        searched_at = datetime.now(UTC).isoformat()
        category = classify_source_group(query) if category == "auto" else category
        if category not in TRUSTED_SOURCE_GROUPS:
            raise ValueError(
                "Trusted source category must be local, science, or economic"
            )
        if not self.enabled:
            return TrustedSearchResult(
                available=False,
                verified=False,
                query=query,
                category=category,
                summary="",
                citations=(),
                searched_at=searched_at,
                warning="Trusted live search is not configured.",
            )

        allowed_domains = TRUSTED_SOURCE_GROUPS[category]
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Use the web-search server tool exactly once. Search only the "
                        "configured trusted domains. Return a concise factual summary "
                        "with dates, geography, and uncertainty. Do not invent sources."
                    ),
                },
                {"role": "user", "content": query[:2000]},
            ],
            "temperature": 0,
            "max_tokens": 550,
            "reasoning": {"effort": "low", "exclude": True},
            "provider": {
                "data_collection": OPENROUTER_DATA_COLLECTION,
                "zdr": OPENROUTER_ENFORCE_ZDR,
            },
            "tools": [
                {
                    "type": "openrouter:web_search",
                    "parameters": {
                        "engine": "exa",
                        "allowed_domains": list(allowed_domains),
                        "max_results": max(1, min(TRUSTED_SEARCH_MAX_RESULTS, 5)),
                        "max_total_results": max(1, min(TRUSTED_SEARCH_MAX_RESULTS, 5)),
                        "search_context_size": "low",
                    },
                }
            ],
        }
        try:
            response = requests.post(
                OPENROUTER_API_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "X-Title": "RAISE trusted-source search",
                },
                json=payload,
                timeout=self.timeout_seconds,
            )
            if response.status_code != 200:
                raise RuntimeError(
                    f"Trusted search returned HTTP {response.status_code}"
                )
            data = response.json()
            message = data["choices"][0]["message"]
            citations = []
            for annotation in message.get("annotations") or []:
                if annotation.get("type") != "url_citation":
                    continue
                citation = annotation.get("url_citation") or {}
                url = str(citation.get("url") or "")
                if not url_is_trusted(url, allowed_domains):
                    continue
                citations.append(
                    {
                        "source_type": "trusted_live",
                        "title": str(citation.get("title") or url)[:300],
                        "url": url,
                        "domain": urlparse(url).hostname,
                        "content": str(citation.get("content") or "")[:4000],
                        "accessed_at": searched_at,
                        "category": category,
                    }
                )
            usage = data.get("usage") or {}
            server_use = usage.get("server_tool_use") or {}
            search_requests = int(server_use.get("web_search_requests") or 0)
            if search_requests > TRUSTED_SEARCH_MAX_CALLS:
                citations = citations[:TRUSTED_SEARCH_MAX_RESULTS]
            return TrustedSearchResult(
                available=True,
                verified=bool(citations),
                query=query,
                category=category,
                summary=str(message.get("content") or "").strip()[:12000],
                citations=tuple(citations),
                searched_at=searched_at,
                search_requests=search_requests,
                warning=None if citations else "No trusted citation was returned.",
            )
        except (
            requests.RequestException,
            KeyError,
            IndexError,
            TypeError,
            ValueError,
            RuntimeError,
        ):
            return TrustedSearchResult(
                available=True,
                verified=False,
                query=query,
                category=category,
                summary="",
                citations=(),
                searched_at=searched_at,
                warning="Trusted live search failed; current information is unverified.",
            )

    @staticmethod
    def verify_url(url: str) -> dict[str, Any]:
        parsed = urlparse(url)
        return {
            "url": url,
            "trusted": url_is_trusted(url),
            "domain": parsed.hostname,
            "registry_version": "2026-08-pilot-v1",
        }
