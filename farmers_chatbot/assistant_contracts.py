"""Versioned contracts shared by every RAISE delivery channel."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

TURN_SCHEMA_VERSION = "2026-08-v2"

Channel = Literal["web", "streamlit", "whatsapp", "mcp", "test"]


@dataclass(frozen=True)
class TurnCapabilities:
    """Server-controlled capabilities for one normalized channel request."""

    allow_artifacts: bool = True
    allow_project_search: bool = True
    allow_live_search: bool = True
    allow_images: bool = True
    allowed_tools: frozenset[str] | None = None
    max_tool_calls: int | None = None
    tool_timeout_seconds: float = 12.0


@dataclass(frozen=True)
class TurnCommand:
    """Canonical input consumed by the assistant engine/coordinator."""

    request_id: str
    actor_id: str
    channel: Channel
    conversation_id: str
    text: str
    project_id: str | None = None
    attachments: tuple[dict[str, Any], ...] = ()
    attachment_references: tuple[dict[str, Any], ...] = ()
    mode: str = "standard"
    model_id: str | None = None
    clarification_style: str = "auto"
    project_instructions: str = ""
    capabilities: TurnCapabilities = field(default_factory=TurnCapabilities)

    def payload_fingerprint_input(self) -> dict[str, Any]:
        """Return stable, secret-free input used for idempotency comparison."""

        return {
            "actor_id": self.actor_id,
            "channel": self.channel,
            "conversation_id": self.conversation_id,
            "project_id": self.project_id,
            "text": self.text,
            "attachment_references": list(
                self.attachment_references or self.attachments
            ),
            "mode": self.mode,
            "model_id": self.model_id,
            "clarification_style": self.clarification_style,
        }


@dataclass
class TurnResult:
    """Canonical terminal result persisted before a completion event is emitted."""

    content: str
    kind: str
    language: str
    model: str | None
    citations: list[dict[str, Any]] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    tools_used: list[str] = field(default_factory=list)
    artifact_ids: list[str] = field(default_factory=list)
    duration_ms: int = 0
    ttft_ms: int | None = None
    stage_durations: dict[str, int] = field(default_factory=dict)
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    estimated_cost_usd: float | None = None
    success: bool = True
    error_type: str | None = None
    follow_up_questions: list[str] = field(default_factory=list)
    provider_calls: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class TurnEvent:
    """Typed SSE-neutral event. Adapters serialize this for their channel."""

    event: str
    data: dict[str, Any] = field(default_factory=dict)
    result: TurnResult | None = None
    schema_version: str = TURN_SCHEMA_VERSION
    turn_id: str | None = None
    request_id: str | None = None
    sequence: int | None = None

    def wire_data(self) -> dict[str, Any]:
        data = dict(self.data)
        data.setdefault("schema_version", self.schema_version)
        if self.turn_id:
            data.setdefault("turn_id", self.turn_id)
        if self.request_id:
            data.setdefault("request_id", self.request_id)
        if self.sequence is not None:
            data.setdefault("sequence", self.sequence)
        return data
