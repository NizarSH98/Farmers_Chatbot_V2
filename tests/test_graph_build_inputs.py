"""Fresh-machine graph bootstrap input contracts."""

from pathlib import Path

import pytest

from farmers_chatbot.graph_build import GraphBuildError, source_manifest_hash

ROOT = Path(__file__).parents[1]
ENGLISH = ROOT / "knowledge_base" / "agrifood_knowledge_v0.3.en.md"
ARABIC = ROOT / "knowledge_base" / "agrifood_knowledge_v0.3.ar.md"
DISPOSITION = ROOT / "knowledge_base" / "agrifood_knowledge_v0.3.disposition.json"


def test_manifest_uses_committed_provenance_when_private_docx_is_absent(
    tmp_path: Path,
) -> None:
    value = source_manifest_hash(
        english=ENGLISH,
        arabic=ARABIC,
        disposition=DISPOSITION,
        source_doc=tmp_path / "not-present.docx",
    )
    assert len(value) == 64


def test_manifest_rejects_a_present_but_changed_source_docx(tmp_path: Path) -> None:
    source = tmp_path / "source.docx"
    source.write_bytes(b"not the approved source")
    with pytest.raises(GraphBuildError, match="checksum changed"):
        source_manifest_hash(
            english=ENGLISH,
            arabic=ARABIC,
            disposition=DISPOSITION,
            source_doc=source,
        )
