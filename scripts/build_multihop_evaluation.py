"""Build cross-passage multi-hop retrieval cases from the active release.

The source-anchored golden set paraphrases one passage per case, so dense and
sparse fusion already reach ~99% recall@10 on it and a graph cannot show any
benefit there. These cases are built the other way round: each one is a
two-hop chain A -r1- B -r2- C whose hops are evidenced in *different*
documents. The prompt names only the endpoints A and C. It never names the
bridge B or either predicate, so lexical overlap with one passage cannot reach
both hops' evidence.

Cases are deterministic for a given release, are written in English, MSA,
Lebanese Arabic, and Arabizi, and validate against `raise.eval.case.v1`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row

from scripts.evaluation.schema import EvaluationCase

GENERATOR_VERSION = "raise.eval.multihop-builder.v1"
DEFAULT_OUTPUT = Path("evaluation/golden/multihop_dev.v1.jsonl")
DEFAULT_MANIFEST = Path("evaluation/golden/multihop_manifest.v1.json")

# Predicates too generic or too operational to make a meaningful farmer question.
EXCLUDED_PREDICATES = frozenset({"related_to", "has_unit", "requires_live_source"})
# A bridge connected to everything ("Akkar", "farm") makes a trivial chain.
MAX_BRIDGE_DEGREE = 15
LANGUAGES: tuple[tuple[str, str, str], ...] = (
    # (case language, language group, tag)
    ("en", "english", "en"),
    ("ar", "arabic", "msa"),
    ("ar-LB", "arabic", "leb"),
    ("ar-LB-Latn", "arabic", "arabizi"),
)
RISK_ORDER = ("low", "medium", "high", "critical")


@dataclass(frozen=True)
class Relation:
    id: str
    subject: str
    predicate: str
    object: str
    risk: str
    chunks: frozenset[str]
    documents: frozenset[str]


@dataclass(frozen=True)
class Chain:
    start: str
    bridge: str
    end: str
    first: Relation
    second: Relation

    @property
    def key(self) -> str:
        return hashlib.sha256(f"{self.first.id}|{self.second.id}".encode()).hexdigest()


def _prompt(language: str, start: dict[str, str], end: dict[str, str]) -> str:
    a_en, c_en = start["en"], end["en"]
    a_ar, c_ar = start["ar"] or a_en, end["ar"] or c_en
    if language == "en":
        return (
            f"On a small farm in Akkar, how is {a_en} connected to {c_en}? "
            "What links them, and what should I do about it?"
        )
    if language == "ar":
        return (
            f"في مزرعة صغيرة في عكار، ما العلاقة بين {a_ar} و{c_ar}؟ "
            "ما الذي يربط بينهما، وماذا يجب أن أفعل؟"
        )
    if language == "ar-LB":
        return (
            f"عندي مزرعة صغيرة بعكار، شو العلاقة بين {a_ar} و{c_ar}؟ "
            "شو اللي بيربطهن ببعض، وشو لازم أعمل؟"
        )
    return (
        f"3ande mazra3a zghire bi 3akkar, shu l 3ale2a bayn {a_en} w {c_en}? "
        "shu yalle byerbothon, w shu lezim e3mel?"
    )


def _load(connection: psycopg.Connection, release_id: str) -> tuple[list[Relation], dict[str, dict[str, str]]]:
    entities = {
        row["id"]: {"en": (row["label_en"] or "").strip(), "ar": (row["label_ar"] or "").strip()}
        for row in connection.execute(
            "SELECT id, label_en, label_ar FROM graph_entities WHERE release_id = %s",
            (release_id,),
        )
    }
    evidence: dict[str, tuple[set[str], set[str]]] = defaultdict(lambda: (set(), set()))
    for row in connection.execute(
        """
        SELECT link.relation_id, link.chunk_id, chunk.document_id
        FROM graph_evidence_links link
        JOIN graph_chunks chunk
          ON chunk.release_id = link.release_id AND chunk.id = link.chunk_id
        WHERE link.release_id = %s AND link.relation_id IS NOT NULL
        """,
        (release_id,),
    ):
        chunks, documents = evidence[row["relation_id"]]
        chunks.add(row["chunk_id"])
        documents.add(row["document_id"])
    relations = []
    for row in connection.execute(
        """
        SELECT id, subject_entity_id, predicate, object_entity_id, risk
        FROM graph_relations
        WHERE release_id = %s AND review_status = 'approved'
          AND object_entity_id IS NOT NULL
        """,
        (release_id,),
    ):
        chunks, documents = evidence.get(row["id"], (set(), set()))
        if not chunks or row["predicate"] in EXCLUDED_PREDICATES:
            continue
        relations.append(
            Relation(
                id=row["id"],
                subject=row["subject_entity_id"],
                predicate=row["predicate"],
                object=row["object_entity_id"],
                risk=str(row["risk"] or "medium"),
                chunks=frozenset(chunks),
                documents=frozenset(documents),
            )
        )
    return relations, entities


def chains(relations: list[Relation]) -> list[Chain]:
    """Two-hop chains whose hops are evidenced in disjoint documents."""

    incident: dict[str, list[Relation]] = defaultdict(list)
    for relation in relations:
        incident[relation.subject].append(relation)
        incident[relation.object].append(relation)
    found: dict[tuple[str, str], Chain] = {}
    for bridge, edges in incident.items():
        if len(edges) > MAX_BRIDGE_DEGREE:
            continue
        for first in edges:
            for second in edges:
                if first.id >= second.id or first.documents & second.documents:
                    continue
                start = first.object if first.subject == bridge else first.subject
                end = second.object if second.subject == bridge else second.subject
                if len({start, bridge, end}) < 3:
                    continue
                chain = Chain(start, bridge, end, first, second)
                pair = tuple(sorted((start, end)))
                if pair not in found or chain.key < found[pair].key:
                    found[pair] = chain
    return sorted(found.values(), key=lambda chain: chain.key)


def select(candidates: list[Chain], limit: int) -> list[Chain]:
    """Deterministic, diverse selection: spread bridges and relations."""

    bridge_use: Counter[str] = Counter()
    relation_use: Counter[str] = Counter()
    chosen: list[Chain] = []
    for chain in candidates:
        if bridge_use[chain.bridge] >= 2:
            continue
        if relation_use[chain.first.id] >= 2 or relation_use[chain.second.id] >= 2:
            continue
        chosen.append(chain)
        bridge_use[chain.bridge] += 1
        relation_use[chain.first.id] += 1
        relation_use[chain.second.id] += 1
        if len(chosen) == limit:
            break
    return chosen


def _case(index: int, chain: Chain, entities: dict[str, dict[str, str]]) -> dict[str, Any]:
    language, group, tag = LANGUAGES[index % len(LANGUAGES)]
    start, end = entities[chain.start], entities[chain.end]
    risk = max((chain.first.risk, chain.second.risk), key=lambda value: RISK_ORDER.index(value) if value in RISK_ORDER else 1)
    relevant = [
        {"evidence_id": f"qdrant:chunk:{chunk}", "relevance": 2}
        for chunk in sorted(chain.first.chunks | chain.second.chunks)
    ]
    return {
        "schema_version": "raise.eval.case.v1",
        "case_id": f"MH-{index + 1:04d}",
        "split": "public_dev",
        "language": language,
        "language_group": group,
        "prompt": _prompt(language, start, end),
        "fixture_only": False,
        "relevant_evidence": relevant,
        "expected_graph_paths": [
            [chain.first.subject, chain.first.predicate, chain.first.object],
            [chain.second.subject, chain.second.predicate, chain.second.object],
        ],
        "claims": [],
        "risk": {"level": risk, "must_escalate": False, "prohibited_actions": []},
        "tags": ["multi_hop_cross_document", "akkar", tag],
    }


def build(database_url: str, limit: int) -> tuple[list[dict[str, Any]], str, int]:
    with psycopg.connect(database_url, row_factory=dict_row) as connection:
        active = connection.execute(
            "SELECT release_id FROM active_knowledge_releases LIMIT 1"
        ).fetchone()
        if not active:
            raise SystemExit("No active knowledge release; run build-graph first.")
        release_id = str(active["release_id"])
        relations, entities = _load(connection, release_id)
    candidates = chains(relations)
    usable = [
        chain for chain in candidates
        if entities.get(chain.start, {}).get("en") and entities.get(chain.end, {}).get("en")
    ]
    cases = [_case(index, chain, entities) for index, chain in enumerate(select(usable, limit))]
    for case in cases:
        EvaluationCase.from_dict(case)
    return cases, release_id, len(usable)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--limit", type=int, default=60)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    database_url = os.getenv("DATABASE_URL", "")
    if not database_url.startswith(("postgres://", "postgresql://")):
        raise SystemExit("DATABASE_URL must point to PostgreSQL")
    cases, release_id, candidates = build(database_url, args.limit)
    body = "".join(json.dumps(case, ensure_ascii=False, sort_keys=True) + "\n" for case in cases)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(body, encoding="utf-8", newline="\n")
    manifest = {
        "schema_version": GENERATOR_VERSION,
        "release_id": release_id,
        "cases": len(cases),
        "candidate_chains": candidates,
        "cases_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "languages": dict(Counter(case["tags"][-1] for case in cases)),
        "review_status": "generated_candidate_needs_agronomist_review",
        "rules": {
            "hops": 2,
            "hop_evidence": "disjoint documents",
            "prompt_names": "endpoints only (no bridge entity, no predicate)",
            "excluded_predicates": sorted(EXCLUDED_PREDICATES),
            "max_bridge_degree": MAX_BRIDGE_DEGREE,
        },
    }
    args.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"cases": len(cases), "candidates": candidates, "release_id": release_id}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
