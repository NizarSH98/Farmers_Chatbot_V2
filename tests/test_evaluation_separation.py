from __future__ import annotations

import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from scripts.evaluation.schema import SchemaError, load_cases
from scripts.evaluation.separation import (
    assert_hidden_not_tracked,
    assert_split_separation,
    normalized_prompt,
    prompt_fingerprint,
)

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "evaluation" / "fixtures" / "public_cases.v1.jsonl"


def hidden_copy(*, same_id: bool = False, same_prompt: bool = False):
    source = load_cases(PUBLIC)[0]
    return replace(
        source,
        case_id=source.case_id if same_id else "HIDDEN-SYN-001",
        split="hidden_test",
        prompt=source.prompt if same_prompt else "Distinct protected synthetic prompt",
        fixture_only=False,
    )


def test_public_and_hidden_splits_must_have_distinct_ids_and_prompts() -> None:
    public = load_cases(PUBLIC)
    result = assert_split_separation(public, (hidden_copy(),))
    assert result["passed"] is True

    with pytest.raises(SchemaError, match="IDs overlap"):
        assert_split_separation(public, (hidden_copy(same_id=True),))
    with pytest.raises(SchemaError, match="prompts overlap"):
        assert_split_separation(public, (hidden_copy(same_prompt=True),))


def test_prompt_fingerprint_normalizes_case_spacing_and_punctuation() -> None:
    assert normalized_prompt(" Alpha, BETA! ") == normalized_prompt("alpha beta")
    assert prompt_fingerprint(" Alpha, BETA! ") == prompt_fingerprint("alpha beta")


def test_hidden_directory_is_ignored_and_contains_no_tracked_fixtures() -> None:
    hidden = ROOT / "evaluation" / "hidden"
    assert_hidden_not_tracked(ROOT, hidden)
    result = subprocess.run(
        ["git", "-C", str(ROOT), "check-ignore", "evaluation/hidden/example.jsonl"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
