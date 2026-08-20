"""Answers must not be cut off by budgets chosen for a smaller-output era."""

from __future__ import annotations

import pytest

from farmers_chatbot.assistant_pipeline import _verifier_token_budget
from farmers_chatbot.config import (
    MODE_PROFILES,
    MODEL_CATALOG,
    model_capability,
    resolve_history_budget,
    resolve_max_tokens,
)

LUNA = "openai/gpt-5.6-luna"


def test_luna_is_catalogued_with_real_provider_limits():
    luna = MODEL_CATALOG[LUNA]
    assert luna.supports_images
    assert luna.context_tokens >= 1_000_000
    assert luna.max_output_tokens >= 100_000


@pytest.mark.parametrize("mode", sorted(MODE_PROFILES))
def test_each_mode_gets_its_full_target_on_a_large_output_model(mode: str) -> None:
    profile = MODE_PROFILES[mode]
    assert resolve_max_tokens(profile.max_tokens, LUNA) == profile.max_tokens


def test_budget_is_clamped_to_a_smaller_models_ceiling():
    """Asking for more than the provider returns wastes a round trip."""

    capped = resolve_max_tokens(100_000, "moonshotai/kimi-k3")
    assert capped == model_capability("moonshotai/kimi-k3").max_output_tokens


def test_unknown_models_fall_back_to_conservative_limits():
    assert resolve_max_tokens(100_000, "someone/not-in-catalog") == 4_096
    assert resolve_history_budget("someone/not-in-catalog") == (16, 12_000)


def test_history_budget_scales_with_the_context_window():
    assert resolve_history_budget(LUNA) > resolve_history_budget("someone/unknown")


def test_verifier_budget_tracks_the_draft_it_must_echo():
    """A fixed cap truncated the verifier JSON, which surfaced as a refusal."""

    short = _verifier_token_budget("x" * 500)
    long = _verifier_token_budget("x" * 40_000)

    assert short >= 2_000
    assert long > short
    assert long <= 32_000
