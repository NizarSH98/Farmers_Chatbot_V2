import json
from pathlib import Path


def test_every_knowledge_item_has_both_languages(knowledge):
    language_pairs = {}
    for document in knowledge.documents:
        language_pairs.setdefault(document.item_id, set()).add(document.language)
    assert language_pairs
    assert all(languages == {"arabic", "english"} for languages in language_pairs.values())


def test_all_referenced_sources_exist(knowledge):
    for document in knowledge.documents:
        for source_id in document.source_ids:
            assert knowledge.get_source(source_id) is not None


def test_bilingual_retrieval_meets_logframe_candidate_target(knowledge):
    cases = [
        json.loads(line)
        for line in Path("evaluation/benchmark_questions.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    results = []
    for case in cases:
        retrieved = {
            result.item_id
            for result in knowledge.search(
                case["question"],
                language=case["language"],
                top_k=5,
            )
        }
        results.append(bool(retrieved & set(case["relevant_ids"])))
    assert sum(results) / len(results) >= 0.8

