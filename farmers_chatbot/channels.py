"""Channel-neutral message contracts for web, Telegram, or WhatsApp adapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class IncomingMessage:
    channel: str
    external_user_id: str
    text: str
    language: str | None = None
    consent_to_pilot_logging: bool = False


@dataclass(frozen=True)
class OutgoingMessage:
    text: str
    source_ids: tuple[str, ...] = ()
    warning: str | None = None


class ChannelAdapter(Protocol):
    """Interface implemented by an approved pilot messaging channel."""

    def receive(self, payload: dict) -> IncomingMessage:
        """Validate and normalize a provider webhook payload."""

    def send(self, recipient_id: str, message: OutgoingMessage) -> None:
        """Send a response through the configured provider."""

