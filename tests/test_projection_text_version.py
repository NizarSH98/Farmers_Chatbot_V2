from __future__ import annotations

from farmers_chatbot.qdrant_projection import projection_search_text
from farmers_chatbot.retrieval_versions import PROJECTION_TEXT_VERSION


def test_arabic_projection_retains_source_and_adds_arabizi() -> None:
    source = "البطاطا تحتاج إدارة ري مناسبة"
    projected = projection_search_text(source, "ar")

    assert projected.startswith(source + "\n")
    assert "albtata" in projected
    assert PROJECTION_TEXT_VERSION.endswith("-arabizi")


def test_english_projection_is_unchanged() -> None:
    source = "potato irrigation management"
    assert projection_search_text(source, "en") == source
