import json
from pathlib import Path

from farmers_chatbot.agrifood_ontology import (
    ENTITIES,
    ONTOLOGY_MIN_ENTITIES,
    ONTOLOGY_MIN_RELATIONS,
    ONTOLOGY_VERSION,
    RELATIONS,
    resolve_ontology_entity,
    validate_ontology,
)
from farmers_chatbot.graph_ingestion import ENTITY_TYPES
from farmers_chatbot.knowledge_markdown import parse_knowledge_markdown
from farmers_chatbot.knowledge_release import build_release_batch

ROOT = Path(__file__).resolve().parents[1]
MARKDOWN = ROOT / "knowledge_base" / "agrifood_knowledge_draft_v0.2.md"
GOLD = ROOT / "evaluation" / "fixtures" / "ontology_gold.v1.json"


def test_ontology_has_bilingual_full_type_and_scale_coverage() -> None:
    corpus = parse_knowledge_markdown(MARKDOWN)
    validate_ontology({str(item.metadata["id"]) for item in corpus.records})
    assert len(ENTITIES) >= ONTOLOGY_MIN_ENTITIES
    assert len(RELATIONS) >= ONTOLOGY_MIN_RELATIONS
    assert {item.entity_type for item in ENTITIES} == set(ENTITY_TYPES)
    assert all(item.label_en and item.label_ar for item in ENTITIES)
    assert {item.metadata["ontology_version"] for item in corpus.records} == {
        ONTOLOGY_VERSION
    }


def test_visible_ontology_gold_is_exact_for_resolution_and_qualifiers() -> None:
    fixture = json.loads(GOLD.read_text(encoding="utf-8"))
    resolved = sum(
        resolve_ontology_entity(item["mention"]) == item["entity"]
        for item in fixture["entity_resolution"]
    )
    assert resolved / len(fixture["entity_resolution"]) >= 0.95

    actual = {
        (
            item.record_id,
            item.subject,
            item.predicate,
            item.object,
            item.risk,
            item.qualifiers.get("basis"),
        )
        for item in RELATIONS
    }
    matched = sum(
        (
            item["record_id"],
            item["subject"],
            item["predicate"],
            item["object"],
            item["risk"],
            item.get("basis"),
        )
        in actual
        for item in fixture["relations"]
    )
    assert matched / len(fixture["relations"]) >= 0.90


def test_release_compiles_every_relation_with_passage_evidence() -> None:
    batch = build_release_batch(MARKDOWN)
    relation_ids = {item.id for item in batch.relations}
    evidence_by_relation = {
        item.relation_id: item for item in batch.evidence if item.relation_id
    }
    chunks = {item.id: item for item in batch.chunks}
    assert len(batch.entities) == len(ENTITIES)
    assert len(batch.relations) == len(RELATIONS)
    assert relation_ids == set(evidence_by_relation)
    assert all(
        evidence.excerpt in chunks[evidence.chunk_id].content
        for evidence in evidence_by_relation.values()
    )
    assert all(item.review_status == "ai_draft" for item in batch.relations)
    assert all(
        item.qualifiers["ontology_version"] == ONTOLOGY_VERSION
        for item in batch.relations
    )
