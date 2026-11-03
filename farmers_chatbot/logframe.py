"""Logframe evidence status loaded from the tracked reports directory."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_logframe_status(
    path: str | Path = "data/logframe_status.json",
) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)
