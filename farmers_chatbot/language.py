"""Small, deterministic language helpers."""

from __future__ import annotations

import re

ARABIC_RE = re.compile(
    r"[\u0600-\u06ff\u0750-\u077f\u08a0-\u08ff\ufb50-\ufdff\ufe70-\ufeff]"
)


def detect_language(text: str) -> str:
    """Return ``arabic`` when more than 30% of letter characters are Arabic."""

    arabic_chars = len(ARABIC_RE.findall(text or ""))
    latin_chars = len(re.findall(r"[A-Za-z]", text or ""))
    total = arabic_chars + latin_chars
    if not total:
        return "english"
    return "arabic" if arabic_chars / total > 0.3 else "english"

