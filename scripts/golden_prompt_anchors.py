"""Deterministic, source-derived prompts for the golden evaluation candidate."""

from __future__ import annotations

import re

_ARABIZI = str.maketrans(
    {
        "ا": "a", "أ": "a", "إ": "i", "آ": "aa", "ب": "b", "ت": "t",
        "ث": "th", "ج": "j", "ح": "7", "خ": "kh", "د": "d", "ذ": "z",
        "ر": "r", "ز": "z", "س": "s", "ش": "sh", "ص": "s", "ض": "d",
        "ط": "t", "ظ": "z", "ع": "3", "غ": "gh", "ف": "f", "ق": "2",
        "ك": "k", "ل": "l", "م": "m", "ن": "n", "ه": "h", "ة": "e",
        "و": "w", "ؤ": "u", "ي": "y", "ى": "a", "ئ": "e", "ء": "2",
    }
)


def first_sentence(text: str, limit: int = 260) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    sentence = re.split(r"(?<=[.!?؟])\s+", normalized, maxsplit=1)[0]
    if len(sentence) <= limit:
        return sentence
    return sentence[:limit].rsplit(" ", 1)[0] + "…"


def anchored_prompt(base_prompt: str, language: str, claim_text: str) -> str:
    """Create a realistic evidence-specific scenario without assigning labels."""

    anchor = first_sentence(claim_text)
    if language == "en":
        lead = f"A farmer reports this situation: {anchor} What should they understand or do? "
    elif language == "arabizi":
        transliterated = re.sub(r"[ًٌٍَُِّْـ]", "", anchor).translate(_ARABIZI)
        lead = f"hayde l 7ale: {transliterated} shu lezim efham aw e3mel? "
    elif language == "code":
        lead = f"بهالحالة الزراعية: {anchor} what is the safe practical decision? "
    elif language == "leb":
        lead = f"بهالحالة: {anchor} شو لازم إفهم أو إعمل بطريقة آمنة؟ "
    else:
        lead = f"في هذه الحالة: {anchor} ما الفهم أو الإجراء العملي الآمن؟ "
    return lead + base_prompt
