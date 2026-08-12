"""Transactional turn lifecycle shared by every delivery-channel adapter."""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any

from .assistant_contracts import TurnCommand, TurnResult
from .pilot_store import PilotStore, TurnReservation

_DEFAULT_RESERVATIONS = {"quick": 0.05, "standard": 0.15, "deep": 0.50}
_TERMINAL_STATUSES = {
    "complete",
    "awaiting_clarification",
    "failed",
    "cancelled",
    "timed_out",
    "refused",
}


class TurnCoordinator:
    """Own idempotency, quota reservation, persistence, and stream recovery."""

    def __init__(self, store: PilotStore) -> None:
        self.store = store

    @staticmethod
    def payload_sha256(command: TurnCommand) -> str:
        normalized = json.dumps(
            command.payload_fingerprint_input(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(normalized).hexdigest()

    @staticmethod
    def reserved_cost(mode: str) -> float:
        setting = f"{mode.upper()}_TURN_RESERVATION_USD"
        fallback = _DEFAULT_RESERVATIONS.get(mode, _DEFAULT_RESERVATIONS["standard"])
        try:
            return max(0.0, float(os.getenv(setting, str(fallback))))
        except ValueError:
            return fallback

    def reserve(
        self,
        command: TurnCommand,
        *,
        language: str,
        stored_attachments: list[dict[str, Any]],
        clarification_count: int,
    ) -> TurnReservation:
        return self.store.reserve_assistant_turn(
            command.actor_id,
            command.conversation_id,
            request_id=command.request_id,
            payload_sha256=self.payload_sha256(command),
            channel=command.channel,
            mode=command.mode,
            language=language,
            user_content=command.text,
            attachments=stored_attachments,
            clarification_count=clarification_count,
            reserved_cost_usd=self.reserved_cost(command.mode),
        )

    def replay(self, command: TurnCommand) -> TurnReservation | None:
        return self.store.find_assistant_turn_by_request(
            command.actor_id,
            command.request_id,
            self.payload_sha256(command),
        )

    def finalize(
        self,
        command: TurnCommand,
        turn_id: str,
        result: TurnResult,
        *,
        analysis: dict[str, Any],
        terminal_sequence: int,
    ) -> str:
        provider_prompt = 0
        provider_completion = 0
        provider_cost = 0.0
        saw_prompt = saw_completion = saw_cost = False
        for record in result.provider_calls:
            usage = record.get("usage") or {}
            if usage.get("prompt_tokens") is not None:
                provider_prompt += int(usage["prompt_tokens"])
                saw_prompt = True
            if usage.get("completion_tokens") is not None:
                provider_completion += int(usage["completion_tokens"])
                saw_completion = True
            if usage.get("cost_usd") is not None:
                provider_cost += float(usage["cost_usd"])
                saw_cost = True
        status = (
            "failed"
            if not result.success
            else "awaiting_clarification"
            if result.kind == "clarification"
            else "refused"
            if result.kind == "refusal"
            else "complete"
        )
        return self.store.finalize_assistant_turn(
            command.actor_id,
            turn_id,
            turn_status=status,
            message_content=result.content,
            message_language=result.language,
            message_mode=command.mode,
            message_model=result.model,
            message_status=result.kind,
            citations=result.citations,
            tools=result.tools_used,
            artifact_ids=result.artifact_ids,
            warning=result.warnings[0] if result.warnings else None,
            analysis=analysis,
            duration_ms=result.duration_ms,
            success=result.success,
            error_type=result.error_type,
            trusted_searches=int("search_trusted_sources" in result.tools_used),
            ttft_ms=result.ttft_ms,
            stage_durations=result.stage_durations,
            prompt_tokens=(
                provider_prompt if saw_prompt else result.prompt_tokens
            ),
            completion_tokens=(
                provider_completion if saw_completion else result.completion_tokens
            ),
            estimated_cost_usd=(
                provider_cost if saw_cost else result.estimated_cost_usd
            ),
            provider_calls=result.provider_calls,
            terminal_sequence=terminal_sequence,
        )

    def fail(
        self,
        actor_id: str,
        turn_id: str,
        *,
        status: str,
        error_type: str,
        duration_ms: int,
        terminal_sequence: int,
    ) -> None:
        self.store.fail_reserved_turn(
            actor_id,
            turn_id,
            status=status,
            error_type=error_type,
            duration_ms=duration_ms,
            terminal_sequence=terminal_sequence,
        )

    def status(self, actor_id: str, turn_id: str) -> dict[str, Any]:
        item = self.store.get_assistant_turn(actor_id, turn_id)
        item["terminal"] = str(item["status"]) in _TERMINAL_STATUSES
        item["error"] = item.pop("error_type", None)
        return item
