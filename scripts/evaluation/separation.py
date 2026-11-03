"""Guards that keep hidden evaluation prompts out of development fixtures."""

from __future__ import annotations

import hashlib
import subprocess
import unicodedata
from pathlib import Path

from .schema import EvaluationCase, SchemaError


def normalized_prompt(prompt: str) -> str:
    normalized = unicodedata.normalize("NFKC", prompt).casefold()
    return "".join(
        character
        for character in normalized
        if not unicodedata.category(character).startswith(("M", "P", "S", "Z"))
    )


def prompt_fingerprint(prompt: str) -> str:
    return hashlib.sha256(normalized_prompt(prompt).encode("utf-8")).hexdigest()


def assert_split_separation(
    public_cases: tuple[EvaluationCase, ...],
    hidden_cases: tuple[EvaluationCase, ...],
) -> dict[str, int | bool]:
    if any(case.split != "public_dev" for case in public_cases):
        raise SchemaError("every public case must declare split=public_dev")
    if any(case.split != "hidden_test" for case in hidden_cases):
        raise SchemaError("every hidden case must declare split=hidden_test")
    public_ids = {case.case_id for case in public_cases}
    hidden_ids = {case.case_id for case in hidden_cases}
    if public_ids & hidden_ids:
        raise SchemaError("public and hidden case IDs overlap")
    public_prompts = {prompt_fingerprint(case.prompt) for case in public_cases}
    hidden_prompts = {prompt_fingerprint(case.prompt) for case in hidden_cases}
    if public_prompts & hidden_prompts:
        raise SchemaError("public and hidden normalized prompts overlap")
    return {
        "passed": True,
        "public_case_count": len(public_cases),
        "hidden_case_count": len(hidden_cases),
    }


def tracked_hidden_files(repo_root: Path, hidden_root: Path) -> tuple[str, ...]:
    repository = repo_root.resolve()
    hidden = hidden_root.resolve()
    try:
        relative = hidden.relative_to(repository)
    except ValueError:
        return ()
    result = subprocess.run(
        ["git", "-C", str(repository), "ls-files", "--", relative.as_posix()],
        check=True,
        capture_output=True,
        text=True,
    )
    return tuple(line for line in result.stdout.splitlines() if line.strip())


def assert_hidden_not_tracked(repo_root: Path, hidden_root: Path) -> None:
    tracked = tracked_hidden_files(repo_root, hidden_root)
    if tracked:
        raise SchemaError("hidden evaluation files are tracked by Git")
