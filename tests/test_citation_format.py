"""Internal evidence IDs must never reach a reader, but attribution must stay."""

from __future__ import annotations

from farmers_chatbot.citation_format import (
    CitationRenderer,
    StreamingCitationRewriter,
    citation_ids,
)

CHUNK = "qdrant:chunk:chunk_2dbc1c7749f59bc1e7920104"
CLAIM = "qdrant:claim:claim_bc71b9e496bd4a229480fd21"


def test_known_ids_become_markers_numbered_by_first_use():
    renderer = CitationRenderer((CHUNK, CLAIM))

    result = renderer.rewrite(
        f"Irrigate at tuber initiation [{CLAIM}]. Soil depth matters [{CHUNK}]. "
        f"See also [{CLAIM}]."
    )

    assert result == (
        "Irrigate at tuber initiation [1]. Soil depth matters [2]. See also [1]."
    )
    assert renderer.numbers == {CLAIM: 1, CHUNK: 2}


def test_unknown_internal_tags_are_removed_not_shown():
    renderer = CitationRenderer((CHUNK,))

    result = renderer.rewrite("Check the field [graph:relation_abc123:1] weekly.")

    assert "graph:relation" not in result
    assert result == "Check the field  weekly."


def test_ordinary_brackets_survive():
    renderer = CitationRenderer((CHUNK,))

    assert renderer.rewrite("Use NPK [15-15-15] fertiliser.") == (
        "Use NPK [15-15-15] fertiliser."
    )


def test_streaming_never_splits_a_tag_across_chunks():
    renderer = CitationRenderer((CHUNK, CLAIM))
    rewriter = StreamingCitationRewriter(renderer)

    text = f"Water early [{CLAIM}] and mulch [{CHUNK}] after."
    emitted = "".join(rewriter.feed(text[i : i + 7]) for i in range(0, len(text), 7))
    emitted += rewriter.flush()

    assert emitted == "Water early [1] and mulch [2] after."
    assert "qdrant" not in emitted


def test_streaming_releases_a_bracket_that_is_not_a_tag():
    rewriter = StreamingCitationRewriter(CitationRenderer())

    emitted = rewriter.feed("Apply [15-15-15") + rewriter.feed("] evenly.")

    assert emitted + rewriter.flush() == "Apply [15-15-15] evenly."


def test_citation_ids_reads_both_identifier_keys():
    assert citation_ids(
        [
            {"item_id": CHUNK, "title": "a"},
            {"evidence_id": CLAIM},
            {"item_id": CHUNK},
            {"title": "no identifier"},
        ]
    ) == (CHUNK, CLAIM)
