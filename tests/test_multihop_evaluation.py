"""Cross-document multi-hop evaluation cases must need both hops' evidence."""

from __future__ import annotations

from scripts.build_multihop_evaluation import (
    MAX_BRIDGE_DEGREE,
    Relation,
    _case,
    chains,
    select,
)
from scripts.evaluation.schema import EvaluationCase


def _relation(rid: str, subject: str, obj: str, document: str, predicate: str = "may_cause") -> Relation:
    return Relation(
        id=rid,
        subject=subject,
        predicate=predicate,
        object=obj,
        risk="medium",
        chunks=frozenset({f"chunk_{rid}"}),
        documents=frozenset({document}),
    )


ENTITIES = {
    "a": {"en": "late frost", "ar": "الصقيع المتأخر"},
    "b": {"en": "flower drop", "ar": "تساقط الأزهار"},
    "c": {"en": "olive yield", "ar": "إنتاج الزيتون"},
}


def test_chains_require_hops_evidenced_in_different_documents():
    same_doc = [_relation("r1", "a", "b", "doc1"), _relation("r2", "b", "c", "doc1")]
    cross_doc = [_relation("r1", "a", "b", "doc1"), _relation("r2", "b", "c", "doc2")]

    assert chains(same_doc) == []
    (chain,) = chains(cross_doc)
    assert (chain.start, chain.bridge, chain.end) in {("a", "b", "c"), ("c", "b", "a")}


def test_hub_bridges_are_skipped():
    spokes = [
        _relation(f"r{index}", "hub", f"leaf{index}", f"doc{index}")
        for index in range(MAX_BRIDGE_DEGREE + 1)
    ]
    assert chains(spokes) == []


def test_prompt_names_endpoints_but_never_the_bridge_or_predicate():
    (chain,) = chains([_relation("r1", "a", "b", "doc1"), _relation("r2", "b", "c", "doc2")])
    for index in range(4):
        case = _case(index, chain, ENTITIES)
        EvaluationCase.from_dict(case)
        prompt = case["prompt"]
        assert "flower drop" not in prompt and "تساقط الأزهار" not in prompt
        assert "may cause" not in prompt and "may_cause" not in prompt
        assert {item["evidence_id"] for item in case["relevant_evidence"]} == {
            "qdrant:chunk:chunk_r1",
            "qdrant:chunk:chunk_r2",
        }
    languages = {_case(index, chain, ENTITIES)["language"] for index in range(4)}
    assert languages == {"en", "ar", "ar-LB", "ar-LB-Latn"}


def test_selection_is_deterministic_and_spreads_bridges():
    relations = [
        _relation("r1", "a", "b", "doc1"),
        _relation("r2", "b", "c", "doc2"),
        _relation("r3", "b", "d", "doc3"),
        _relation("r4", "b", "e", "doc4"),
    ]
    first = select(chains(relations), limit=10)
    second = select(chains(list(reversed(relations))), limit=10)
    assert [chain.key for chain in first] == [chain.key for chain in second]
    assert len(first) <= 2  # one bridge may anchor at most two cases
