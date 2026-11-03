"""Describe the shape of the active knowledge graph.

Retrieval metrics say whether the graph helps answer questions. They say nothing
about whether the graph is well formed. A release can score well while most of
its entities are orphans, most relations use two of the declared types, or the
alias table collides. This reports that structure so the corpus can be judged
independently of the retrieval score.

    python -m scripts.profile_graph
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from farmers_chatbot.agrifood_ontology import ONTOLOGY_VERSION


def _rows(connection: Any, sql: str, params: tuple[Any, ...] = ()) -> list[dict]:
    return [dict(row) for row in connection.execute(sql, params).fetchall()]


def profile(database_url: str, deployment_scope: str = "pilot") -> dict[str, Any]:
    with psycopg.connect(database_url, row_factory=dict_row) as connection:
        active = connection.execute(
            "SELECT release_id FROM active_knowledge_releases WHERE deployment_scope=%s",
            (deployment_scope,),
        ).fetchone()
        if not active:
            raise RuntimeError(f"no active release for scope {deployment_scope!r}")
        release_id = str(active["release_id"])

        counts = {
            name: int(
                connection.execute(
                    f"SELECT COUNT(*) AS n FROM {table} WHERE release_id=%s",
                    (release_id,),
                ).fetchone()["n"]
            )
            for name, table in (
                ("sources", "graph_sources"),
                ("documents", "graph_documents"),
                ("chunks", "graph_chunks"),
                ("claims", "graph_claims"),
                ("entities", "graph_entities"),
                ("aliases", "graph_entity_aliases"),
                ("relations", "graph_relations"),
                ("evidence_links", "graph_evidence_links"),
            )
        }

        degrees = Counter()
        for row in _rows(
            connection,
            """
            SELECT subject_entity_id AS a, object_entity_id AS b
            FROM graph_relations WHERE release_id=%s
            """,
            (release_id,),
        ):
            if row["a"]:
                degrees[str(row["a"])] += 1
            if row["b"]:
                degrees[str(row["b"])] += 1

        entity_ids = {
            str(row["id"])
            for row in _rows(
                connection,
                "SELECT id FROM graph_entities WHERE release_id=%s",
                (release_id,),
            )
        }
        orphans = sorted(entity_ids - set(degrees))
        degree_values = [degrees.get(entity, 0) for entity in entity_ids]

        relation_types = Counter(
            str(row["predicate"])
            for row in _rows(
                connection,
                "SELECT predicate FROM graph_relations WHERE release_id=%s",
                (release_id,),
            )
        )
        entity_types = Counter(
            str(row["entity_type"])
            for row in _rows(
                connection,
                "SELECT entity_type FROM graph_entities WHERE release_id=%s",
                (release_id,),
            )
        )
        alias_rows = _rows(
            connection,
            """
            SELECT alias, entity_id FROM graph_entity_aliases WHERE release_id=%s
            """,
            (release_id,),
        )

    alias_targets: dict[str, set[str]] = {}
    for row in alias_rows:
        alias_targets.setdefault(
            str(row["alias"]).casefold(), set()
        ).add(str(row["entity_id"]))
    collisions = {
        alias: sorted(targets)
        for alias, targets in alias_targets.items()
        if len(targets) > 1
    }

    return {
        "schema_version": "raise.graph-profile.v1",
        "release_id": release_id,
        "ontology_version": ONTOLOGY_VERSION,
        "counts": counts,
        "connectivity": {
            "entities_with_no_relation": len(orphans),
            "orphan_percent": round(
                100.0 * len(orphans) / max(1, len(entity_ids)), 2
            ),
            "degree_mean": round(statistics.fmean(degree_values), 3)
            if degree_values
            else 0.0,
            "degree_median": statistics.median(degree_values) if degree_values else 0,
            "degree_max": max(degree_values) if degree_values else 0,
            "relations_per_chunk": round(
                counts["relations"] / max(1, counts["chunks"]), 3
            ),
            "sample_orphan_entities": orphans[:10],
        },
        "coverage": {
            "distinct_relation_types_used": len(relation_types),
            "distinct_entity_types_used": len(entity_types),
            "most_common_relation_types": relation_types.most_common(10),
            "most_common_entity_types": entity_types.most_common(10),
            # A graph dominated by one predicate is a taxonomy, not a graph.
            "top_relation_share_percent": round(
                100.0
                * (relation_types.most_common(1)[0][1] if relation_types else 0)
                / max(1, counts["relations"]),
                2,
            ),
        },
        "aliases": {
            "total": len(alias_rows),
            "ambiguous_alias_count": len(collisions),
            "sample_ambiguous": dict(list(collisions.items())[:10]),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", default="pilot")
    parser.add_argument(
        "--output", type=Path, default=Path("build-reports/graph-profile.v1.json")
    )
    args = parser.parse_args()

    database_url = os.getenv("DATABASE_URL", "")
    if not database_url.startswith(("postgres://", "postgresql://")):
        raise SystemExit("DATABASE_URL must point to PostgreSQL")
    report = profile(database_url, args.scope)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
