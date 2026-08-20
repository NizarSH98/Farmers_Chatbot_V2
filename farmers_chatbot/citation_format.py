"""Turn internal evidence IDs in answer text into reader-facing markers.

The model is asked to cite RAISE knowledge with the exact square-bracket ID it
was shown, e.g. `[qdrant:claim:claim_bc71b9e4...]`. That is what makes a specific
sentence attributable, and the verifier relies on it, but it is unreadable.

Deleting the tags would lose per-sentence attribution, which is the point of the
product. Instead each distinct evidence ID becomes a compact `[n]` marker
numbered by first appearance, and the caller maps `n` back to the source card.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Evidence-shaped tags the model may emit. Used only to remove leftovers that do
# not match a known ID, so a stray internal identifier never reaches a farmer.
_EVIDENCE_SHAPED = re.compile(
    r"\[(?:qdrant|graph|kb|project|live|chunk|claim|relation|evidence)"
    r":[^\]\n]{1,160}\]",
    re.IGNORECASE,
)
# Longest plausible tag, used to decide how much of a stream tail to hold back.
_MAX_TAG_LENGTH = 200


@dataclass
class CitationRenderer:
    """Rewrite evidence IDs to `[n]`, numbered by order of first appearance."""

    known_ids: tuple[str, ...] = ()
    _numbers: dict[str, int] = field(default_factory=dict, init=False)
    _pattern: re.Pattern[str] | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        unique = [value for value in dict.fromkeys(self.known_ids) if value]
        if unique:
            # Longest first so `a:b:c` wins over a shorter prefix of itself.
            alternatives = "|".join(
                re.escape(value) for value in sorted(unique, key=len, reverse=True)
            )
            self._pattern = re.compile(rf"\[\s*(?:{alternatives})\s*\]")

    @property
    def numbers(self) -> dict[str, int]:
        """Evidence ID to marker number, for the ids actually cited."""

        return dict(self._numbers)

    def rewrite(self, text: str) -> str:
        if not text:
            return text
        if self._pattern is not None:
            text = self._pattern.sub(self._replace, text)
        # Anything still shaped like an internal identifier is not something a
        # reader should see, and it has no source card to point at.
        return _EVIDENCE_SHAPED.sub("", text)

    def _replace(self, match: re.Match[str]) -> str:
        identifier = match.group(0)[1:-1].strip()
        number = self._numbers.get(identifier)
        if number is None:
            number = len(self._numbers) + 1
            self._numbers[identifier] = number
        return f"[{number}]"


class StreamingCitationRewriter:
    """Apply `CitationRenderer` to a token stream without splitting a tag.

    A tag can straddle two chunks, so any text from an unclosed `[` onward is
    held back until the tag closes or it grows too long to be one.
    """

    def __init__(self, renderer: CitationRenderer) -> None:
        self.renderer = renderer
        self._buffer = ""

    def feed(self, chunk: str) -> str:
        self._buffer += chunk
        opening = self._buffer.rfind("[")
        if opening == -1 or "]" in self._buffer[opening:]:
            release, self._buffer = self._buffer, ""
        elif len(self._buffer) - opening > _MAX_TAG_LENGTH:
            # Too long to be a tag; stop holding it.
            release, self._buffer = self._buffer, ""
        else:
            release, self._buffer = self._buffer[:opening], self._buffer[opening:]
        return self.renderer.rewrite(release)

    def flush(self) -> str:
        release, self._buffer = self._buffer, ""
        return self.renderer.rewrite(release)


def citation_ids(citations: list[dict]) -> tuple[str, ...]:
    """Collect every identifier the model could have been shown for a turn."""

    identifiers: list[str] = []
    for citation in citations:
        for key in ("item_id", "evidence_id"):
            value = citation.get(key)
            if isinstance(value, str) and value:
                identifiers.append(value)
    return tuple(dict.fromkeys(identifiers))
