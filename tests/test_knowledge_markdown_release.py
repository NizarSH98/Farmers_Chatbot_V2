from __future__ import annotations

from pathlib import Path

from farmers_chatbot.knowledge_markdown import parse_knowledge_markdown
from farmers_chatbot.knowledge_release import build_release_batch
from scripts.convert_agrifood_docx import (
    SOURCE_SHA256,
    SPECS,
    DraftRecord,
    render_markdown,
    validate_output,
)


def _records() -> list[DraftRecord]:
    records = []
    for index, spec in enumerate(SPECS, start=1):
        marker = f"{spec.record_id}-{index}"
        records.append(
            DraftRecord(
                spec=spec,
                english_guidance=f"English guidance {marker}.",
                decision_logic=f"Decision logic {marker}.",
                safe_next_action=f"Safe next action {marker}.",
                avoid_escalate=f"Avoid or escalate {marker}.",
                applicability_limits=f"Applicability limits {marker}.",
                source_ids=("TEST-SOURCE",),
                supersedes=(),
                translation={
                    "title_ar": f"عنوان عربي {index}",
                    "guidance_ar": f"إرشادات عربية {marker}",
                    "decision_logic_ar": f"منطق قرار عربي {marker}",
                    "safe_next_action_ar": f"خطوة آمنة عربية {marker}",
                    "avoid_escalate_ar": f"تجنّب أو صعّد بالعربية {marker}",
                    "applicability_limits_ar": f"حدود التطبيق بالعربية {marker}",
                },
            )
        )
    return records


def test_render_parse_and_build_release_are_consistent(tmp_path: Path) -> None:
    records = _records()
    sources = {
        "TEST-SOURCE": {
            "id": "TEST-SOURCE",
            "title": "Synthetic source",
            "publisher": "Test publisher",
            "url": "https://example.org/source",
            "source_class": "A",
        }
    }
    text = render_markdown(records, sources, "source.docx")
    validate_output(text, records, sources)
    path = tmp_path / "corpus.md"
    path.write_text(text, encoding="utf-8")

    corpus = parse_knowledge_markdown(path)
    assert len(corpus.records) == len(SPECS)
    assert corpus.front_matter["source_doc_sha256"] == SOURCE_SHA256
    assert corpus.sources["TEST-SOURCE"]["retrieval_enabled"] is False

    batch = build_release_batch(path)
    assert len(batch.documents) == len(SPECS) * 2
    assert batch.release.review_policy == "draft_allowed"
    assert all(chunk.embedding is None for chunk in batch.chunks)
    assert all(claim.review_status == "ai_draft" for claim in batch.claims)
    assert {item.predicate for item in batch.relations}
