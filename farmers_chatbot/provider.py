"""Single OpenRouter boundary with per-stage usage and latency accounting."""

from __future__ import annotations

import json
import os
import time
from collections.abc import AsyncIterator, Callable
from dataclasses import asdict, dataclass, field
from typing import Any

import httpx

from .config import (
    APP_PUBLIC_URL,
    OPENROUTER_API_URL,
    OPENROUTER_DATA_COLLECTION,
    OPENROUTER_ENFORCE_ZDR,
)

OPENROUTER_EMBEDDINGS_URL = os.getenv(
    "OPENROUTER_EMBEDDINGS_URL", "https://openrouter.ai/api/v1/embeddings"
)


@dataclass(frozen=True)
class ProviderUsage:
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    cost_usd: float | None = None


@dataclass
class ProviderCallRecord:
    stage: str
    model: str
    duration_ms: int
    outcome: str
    usage: ProviderUsage = field(default_factory=ProviderUsage)
    error_type: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["usage"] = asdict(self.usage)
        return result


@dataclass
class ProviderResponse:
    message: dict[str, Any]
    usage: ProviderUsage
    raw: dict[str, Any]


@dataclass
class EmbeddingResponse:
    embeddings: list[list[float]]
    usage: ProviderUsage
    model: str
    raw: dict[str, Any]


class ProviderClient:
    """The only asynchronous HTTP client allowed to call OpenRouter."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        client: httpx.AsyncClient | None = None,
        on_record: Callable[[ProviderCallRecord], None] | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else os.getenv(
            "OPENROUTER_API_KEY", ""
        )
        self._client = client or httpx.AsyncClient(
            timeout=httpx.Timeout(45.0, connect=8.0),
            limits=httpx.Limits(max_connections=60, max_keepalive_connections=20),
            http2=True,
        )
        self._owns_client = client is None
        self._on_record = on_record
        self.records: list[ProviderCallRecord] = []

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def complete(
        self,
        *,
        stage: str,
        payload: dict[str, Any],
        timeout: float = 45.0,
    ) -> ProviderResponse:
        if not self.api_key:
            raise RuntimeError("OpenRouter is not configured")
        request_payload = self._with_policy(payload)
        model = str(request_payload.get("model") or "unknown")
        started = time.perf_counter()
        try:
            response = await self._client.post(
                OPENROUTER_API_URL,
                headers=self.headers(),
                json=request_payload,
                timeout=timeout,
            )
            response.raise_for_status()
            raw = response.json()
            message = raw["choices"][0]["message"]
            usage = self._usage(raw.get("usage") or {})
            self._record(
                ProviderCallRecord(
                    stage=stage,
                    model=model,
                    duration_ms=self._elapsed(started),
                    outcome="success",
                    usage=usage,
                )
            )
            return ProviderResponse(message=dict(message), usage=usage, raw=raw)
        except Exception as exc:
            self._record(
                ProviderCallRecord(
                    stage=stage,
                    model=model,
                    duration_ms=self._elapsed(started),
                    outcome="failed",
                    error_type=type(exc).__name__,
                )
            )
            raise

    async def stream(
        self,
        *,
        stage: str,
        payload: dict[str, Any],
    ) -> AsyncIterator[dict[str, Any]]:
        """Yield normalized content/tool/citation/usage events from one call."""

        if not self.api_key:
            raise RuntimeError("OpenRouter is not configured")
        request_payload = self._with_policy(payload)
        request_payload["stream"] = True
        request_payload.setdefault("stream_options", {"include_usage": True})
        model = str(request_payload.get("model") or "unknown")
        started = time.perf_counter()
        usage = ProviderUsage()
        try:
            async with self._client.stream(
                "POST",
                OPENROUTER_API_URL,
                headers=self.headers(),
                json=request_payload,
            ) as response:
                if response.status_code != 200:
                    body = (await response.aread())[:500]
                    raise ValueError(
                        f"OpenRouter HTTP {response.status_code}: "
                        f"{body.decode('utf-8', errors='replace')}"
                    )
                async for line in response.aiter_lines():
                    if not line or line.startswith(":") or not line.startswith("data:"):
                        continue
                    raw_line = line[5:].strip()
                    if raw_line == "[DONE]":
                        break
                    data = json.loads(raw_line)
                    if data.get("usage"):
                        usage = self._usage(data["usage"])
                        yield {"type": "usage", "usage": data["usage"]}
                    choices = data.get("choices") or []
                    if not choices:
                        continue
                    choice = choices[0]
                    delta = choice.get("delta") or {}
                    if choice.get("finish_reason"):
                        yield {
                            "type": "finish",
                            "finish_reason": choice.get("finish_reason"),
                        }
                    content = delta.get("content")
                    if isinstance(content, str) and content:
                        yield {"type": "content", "text": content}
                    for tool_call in delta.get("tool_calls") or []:
                        yield {"type": "tool_call.delta", "tool_call": tool_call}
                    for annotation in delta.get("annotations") or []:
                        yield {"type": "annotation", "annotation": annotation}
            self._record(
                ProviderCallRecord(
                    stage=stage,
                    model=model,
                    duration_ms=self._elapsed(started),
                    outcome="success",
                    usage=usage,
                )
            )
        except Exception as exc:
            self._record(
                ProviderCallRecord(
                    stage=stage,
                    model=model,
                    duration_ms=self._elapsed(started),
                    outcome="failed",
                    usage=usage,
                    error_type=type(exc).__name__,
                )
            )
            raise

    async def embed(
        self,
        *,
        stage: str,
        inputs: list[str],
        model: str,
        dimensions: int | None = None,
        input_type: str = "search_query",
        timeout: float = 30.0,
    ) -> EmbeddingResponse:
        """Generate a bounded batch through the same audited provider boundary."""

        if not self.api_key:
            raise RuntimeError("OpenRouter is not configured")
        if not inputs or len(inputs) > 64:
            raise ValueError("Embedding batch must contain 1-64 inputs")
        payload: dict[str, Any] = {
            "model": model,
            "input": [str(item)[:16000] for item in inputs],
            "input_type": input_type,
            "encoding_format": "float",
            "provider": self.policy(),
        }
        if dimensions is not None:
            payload["dimensions"] = int(dimensions)
        started = time.perf_counter()
        try:
            response = await self._client.post(
                OPENROUTER_EMBEDDINGS_URL,
                headers=self.headers(),
                json=payload,
                timeout=timeout,
            )
            response.raise_for_status()
            raw = response.json()
            ordered = sorted(raw.get("data") or [], key=lambda item: item["index"])
            embeddings = [
                [float(value) for value in item["embedding"]] for item in ordered
            ]
            if len(embeddings) != len(inputs):
                raise ValueError("Embedding response count does not match input count")
            if dimensions is not None and any(
                len(embedding) != dimensions for embedding in embeddings
            ):
                raise ValueError("Embedding response dimension mismatch")
            usage = self._usage(raw.get("usage") or {})
            self._record(
                ProviderCallRecord(
                    stage=stage,
                    model=model,
                    duration_ms=self._elapsed(started),
                    outcome="success",
                    usage=usage,
                )
            )
            return EmbeddingResponse(
                embeddings=embeddings,
                usage=usage,
                model=str(raw.get("model") or model),
                raw=raw,
            )
        except Exception as exc:
            self._record(
                ProviderCallRecord(
                    stage=stage,
                    model=model,
                    duration_ms=self._elapsed(started),
                    outcome="failed",
                    error_type=type(exc).__name__,
                )
            )
            raise

    def headers(self) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Title": "RAISE agricultural assistant",
        }
        if APP_PUBLIC_URL:
            headers["HTTP-Referer"] = APP_PUBLIC_URL
        return headers

    @staticmethod
    def policy() -> dict[str, Any]:
        return {
            "data_collection": OPENROUTER_DATA_COLLECTION,
            "zdr": OPENROUTER_ENFORCE_ZDR,
        }

    def _with_policy(self, payload: dict[str, Any]) -> dict[str, Any]:
        result = dict(payload)
        result.setdefault("provider", self.policy())
        return result

    def _record(self, record: ProviderCallRecord) -> None:
        self.records.append(record)
        if self._on_record:
            self._on_record(record)

    @staticmethod
    def _usage(value: dict[str, Any]) -> ProviderUsage:
        return ProviderUsage(
            prompt_tokens=ProviderClient._int_or_none(
                value.get("prompt_tokens") or value.get("input_tokens")
            ),
            completion_tokens=ProviderClient._int_or_none(
                value.get("completion_tokens") or value.get("output_tokens")
            ),
            cost_usd=ProviderClient._float_or_none(value.get("cost")),
        )

    @staticmethod
    def _elapsed(started: float) -> int:
        return int((time.perf_counter() - started) * 1000)

    @staticmethod
    def _int_or_none(value: Any) -> int | None:
        try:
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _float_or_none(value: Any) -> float | None:
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None
