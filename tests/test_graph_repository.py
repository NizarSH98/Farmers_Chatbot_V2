from __future__ import annotations

from contextlib import contextmanager
from typing import Any

import pytest
from test_graph_ingestion import _batch

from farmers_chatbot.graph_repository import (
    GraphIntegrityError,
    GraphRepository,
)


class _Cursor:
    def __init__(
        self,
        row: dict[str, Any] | None = None,
        rows: list[dict[str, Any]] | None = None,
        rowcount: int = 1,
    ) -> None:
        self._row = row
        self._rows = rows or []
        self.rowcount = rowcount

    def fetchone(self) -> dict[str, Any] | None:
        return self._row

    def fetchall(self) -> list[dict[str, Any]]:
        return self._rows


class _GraphConnection:
    def __init__(self) -> None:
        self.releases = {
            "old": {
                "state": "ready",
                "publication_scope": "pilot",
                "review_policy": "draft_allowed",
            },
            "new": {
                "state": "ready",
                "publication_scope": "pilot",
                "review_policy": "draft_allowed",
            },
        }
        self.pointer: dict[str, str] = {"pilot": "old"}
        self.activations: list[dict[str, Any]] = []
        self.statements: list[tuple[str, tuple[Any, ...] | None]] = []
        self.search_rows: list[dict[str, Any]] = []

    def execute(
        self,
        statement: str,
        parameters: tuple[Any, ...] | None = None,
    ) -> _Cursor:
        compact = " ".join(statement.lower().split())
        self.statements.append((compact, parameters))
        parameters = parameters or ()
        if "select pg_advisory_xact_lock" in compact:
            return _Cursor()
        if "select state, publication_scope, review_policy" in compact:
            return _Cursor(self.releases.get(str(parameters[0])))
        if compact.startswith("select state from knowledge_releases"):
            release = self.releases.get(str(parameters[0]))
            return _Cursor({"state": release["state"]} if release else None)
        if "select release_id from active_knowledge_releases" in compact:
            release_id = self.pointer.get(str(parameters[0]))
            return _Cursor({"release_id": release_id} if release_id else None)
        if "select previous_release_id" in compact:
            scope, release_id = map(str, parameters[:2])
            matches = [
                item
                for item in self.activations
                if item["scope"] == scope and item["release_id"] == release_id
            ]
            previous = matches[-1]["previous"] if matches else None
            return _Cursor(
                {"previous_release_id": previous} if matches else None
            )
        if compact.startswith("insert into knowledge_release_activations"):
            self.activations.append(
                {
                    "scope": str(parameters[0]),
                    "release_id": str(parameters[1]),
                    "previous": parameters[2],
                }
            )
            return _Cursor()
        if compact.startswith("insert into active_knowledge_releases"):
            self.pointer[str(parameters[0])] = str(parameters[1])
            return _Cursor()
        if compact.startswith("update active_knowledge_releases"):
            self.pointer[str(parameters[2])] = str(parameters[0])
            return _Cursor()
        if "select * from hybrid_search_knowledge_v2" in compact:
            return _Cursor(rows=self.search_rows)
        return _Cursor()


class _Factory:
    def __init__(self, connection: _GraphConnection) -> None:
        self.connection = connection
        self.transactions = 0

    @contextmanager
    def connect(self):
        self.transactions += 1
        yield self.connection


def test_activation_and_rollback_each_use_one_atomic_transaction() -> None:
    connection = _GraphConnection()
    factory = _Factory(connection)
    repository = GraphRepository(factory.connect)

    activation = repository.activate_release(
        "pilot", "new", activated_by="reviewer@example.org"
    )
    assert activation.previous_release_id == "old"
    assert connection.pointer["pilot"] == "new"
    assert factory.transactions == 1

    rollback = repository.rollback_release(
        "pilot", activated_by="reviewer@example.org"
    )
    assert rollback.rolled_back is True
    assert rollback.release_id == "old"
    assert rollback.previous_release_id == "new"
    assert connection.pointer["pilot"] == "old"
    assert factory.transactions == 2


def test_production_activation_requires_production_approved_release() -> None:
    connection = _GraphConnection()
    repository = GraphRepository(_Factory(connection).connect)
    with pytest.raises(GraphIntegrityError, match="approved-only production"):
        repository.activate_release(
            "production", "new", activated_by="reviewer@example.org"
        )


def test_ingestion_batch_writes_every_record_in_one_transaction() -> None:
    batch = _batch()
    connection = _GraphConnection()
    connection.releases[batch.release.id] = {
        "state": "building",
        "publication_scope": "pilot",
        "review_policy": "draft_allowed",
    }
    factory = _Factory(connection)
    repository = GraphRepository(factory.connect)
    counts = repository.ingest_batch(batch)

    assert factory.transactions == 1
    assert counts == {
        "sources": 1,
        "documents": 1,
        "chunks": 1,
        "entities": 2,
        "claims": 1,
        "relations": 1,
        "evidence": 2,
    }
    statements = "\n".join(statement for statement, _ in connection.statements)
    for table in (
        "graph_sources",
        "graph_documents",
        "graph_chunks",
        "graph_entities",
        "graph_entity_aliases",
        "graph_claims",
        "graph_relations",
        "graph_evidence_links",
    ):
        assert f"insert into {table}" in statements


def test_hybrid_search_calls_versioned_function_with_bounded_limit() -> None:
    connection = _GraphConnection()
    connection.search_rows = [{"evidence_id": "chunk:release:one", "score": 0.2}]
    repository = GraphRepository(_Factory(connection).connect)
    rows = repository.hybrid_search(
        release_id="release",
        query="potato pest",
        embedding=None,
        embedding_model=None,
        embedding_dimensions=None,
        top_k=500,
        review_statuses=("approved",),
    )
    assert rows[0]["evidence_id"] == "chunk:release:one"
    statement, parameters = connection.statements[-1]
    assert "hybrid_search_knowledge_v2" in statement
    assert parameters and parameters[5] == 50


def test_graph_paths_are_bidirectional_cycle_safe_and_bounded() -> None:
    connection = _GraphConnection()
    repository = GraphRepository(_Factory(connection).connect)
    assert (
        repository.graph_paths(
            release_id="release",
            entity_ids=("entity-one",),
            max_hops=20,
            review_statuses=("approved",),
            limit=500,
        )
        == []
    )
    statement, parameters = connection.statements[-1]
    assert "relation.object_entity_id = any" in statement
    assert "next.object_entity_id = paths.frontier_entity" in statement
    assert "not walk.next_entity = any(paths.entity_path)" in statement
    assert "limit %s" in statement
    assert parameters and parameters[6] == 2
    assert parameters[-1] == 100


def test_alias_resolution_uses_token_boundaries() -> None:
    connection = _GraphConnection()
    repository = GraphRepository(_Factory(connection).connect)
    assert repository.resolve_entities(
        release_id="release",
        query="pesticide EC test",
    ) == []
    statement, parameters = connection.statements[-1]
    assert "' ' || alias.normalized_alias || ' '" in statement
    assert parameters and parameters[1] == "pesticide ec test"
