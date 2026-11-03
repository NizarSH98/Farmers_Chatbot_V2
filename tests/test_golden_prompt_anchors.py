from scripts.golden_prompt_anchors import anchored_prompt, first_sentence


def test_first_sentence_is_bounded() -> None:
    value = first_sentence("First useful fact. Second unrelated fact.")
    assert value == "First useful fact."


def test_arabizi_anchor_is_source_derived_and_has_no_arabic_script() -> None:
    value = anchored_prompt("shu lezim?", "arabizi", "الماء مهم للمحصول. معلومة ثانية.")
    assert "lma2" in value
    assert "معلومة" not in value


def test_arabic_and_english_anchors_preserve_source_fact() -> None:
    assert "soil test" in anchored_prompt("What next?", "en", "Use a soil test first.")
    assert "فحص التربة" in anchored_prompt("ما الخطوة؟", "msa", "ابدأ بفحص التربة.")
