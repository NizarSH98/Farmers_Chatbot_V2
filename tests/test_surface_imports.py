"""Guard every entry point's imports without executing its module-level setup.

`mcp_server.py` builds its store, gateway, and registry at import time, so it
needs PostgreSQL and cannot simply be imported here. That let it keep passing
`compileall` — which only checks syntax — while importing a name that had been
deleted. This resolves each imported name statically instead.
"""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ENTRY_POINTS = ["mcp_server.py"]


def _project_imports(path: Path) -> list[tuple[str, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: list[tuple[str, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith(
            "farmers_chatbot"
        ):
            found.extend((node.module or "", alias.name) for alias in node.names)
    return found


@pytest.mark.parametrize("entry_point", ENTRY_POINTS)
def test_entry_point_imports_resolve(entry_point: str) -> None:
    imports = _project_imports(ROOT / entry_point)
    assert imports, f"{entry_point} imports nothing from farmers_chatbot"
    missing = [
        f"{module}.{name}"
        for module, name in imports
        if not hasattr(importlib.import_module(module), name)
    ]
    assert not missing, f"{entry_point} imports names that no longer exist: {missing}"
