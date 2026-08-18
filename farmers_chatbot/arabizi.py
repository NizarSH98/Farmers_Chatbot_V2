"""Deterministic Arabic-script to Arabizi search aliases.

This is intentionally a search canonicalizer, not a claim of linguistic
translation. Human-authored Lebanese aliases remain authoritative and are kept
alongside these generated recall aliases.
"""

from __future__ import annotations

import re

_DIACRITICS = re.compile(r"[ًٌٍَُِّْـ]")
_TO_ARABIZI = str.maketrans(
    {
        "ا": "a", "أ": "a", "إ": "i", "آ": "aa", "ب": "b", "ت": "t",
        "ث": "th", "ج": "j", "ح": "7", "خ": "kh", "د": "d", "ذ": "z",
        "ر": "r", "ز": "z", "س": "s", "ش": "sh", "ص": "s", "ض": "d",
        "ط": "t", "ظ": "z", "ع": "3", "غ": "gh", "ف": "f", "ق": "2",
        "ك": "k", "ل": "l", "م": "m", "ن": "n", "ه": "h", "ة": "e",
        "و": "w", "ؤ": "u", "ي": "y", "ى": "a", "ئ": "e", "ء": "2",
    }
)


def arabic_to_arabizi(text: str) -> str:
    value = _DIACRITICS.sub("", text).translate(_TO_ARABIZI)
    return re.sub(r"\s+", " ", value).strip().casefold()
