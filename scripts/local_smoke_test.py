"""Fail-closed local release smoke test for PostgreSQL, Qdrant, and retrieval."""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any
from urllib.request import urlopen

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from qdrant_client import AsyncQdrantClient

from farmers_chatbot.graph_repository import GraphRepository
from farmers_chatbot.migration_status import EXPECTED_DATABASE_REVISION
from farmers_chatbot.qdrant_projection import (
    ProjectionConfig,
    QdrantProjectionRepository,
)
from farmers_chatbot.qdrant_retrieval import QdrantGraphRetrieval
from farmers_chatbot.retrieval import EvidenceBundle, RetrievalRequest, RetrievalService


class _NoFallback(RetrievalService):
    async def retrieve(
        self,
        request: RetrievalRequest,
        *,
        project_chunks: list[dict[str, Any]] | None = None,
    ) -> EvidenceBundle:
        raise RuntimeError("smoke test refuses silent retrieval fallback")


async def run() -> dict[str, Any]:
    api_url = os.getenv("API_INTERNAL_URL", "http://127.0.0.1:8000").rstrip("/")
    agreement_check = await asyncio.to_thread(_check_legal_api, api_url)
    database_url = os.getenv("DATABASE_URL", "")
    config = ProjectionConfig.from_env()
    with psycopg.connect(database_url, row_factory=dict_row) as connection:
        revision = connection.execute("SELECT version_num FROM alembic_version").fetchone()["version_num"]
        row = connection.execute(
            """
            SELECT active.release_id, projection.*
            FROM active_knowledge_releases active
            JOIN knowledge_release_projections projection
              ON projection.release_id=active.release_id AND projection.target='qdrant'
            WHERE active.deployment_scope='pilot'
            """
        ).fetchone()
    if revision != EXPECTED_DATABASE_REVISION:
        raise RuntimeError(f"migration mismatch: {revision} != {EXPECTED_DATABASE_REVISION}")
    if not row or row["state"] != "ready":
        raise RuntimeError("pilot projection is not ready")
    qdrant = AsyncQdrantClient(url=config.url, api_key=config.api_key)
    try:
        evidence_count = (await qdrant.count(row["evidence_collection"], exact=True)).count
        entity_count = (await qdrant.count(row["entity_collection"], exact=True)).count
        aliases = {item.alias_name: item.collection_name for item in (await qdrant.get_aliases()).aliases}
    finally:
        await qdrant.close()
    if evidence_count != row["evidence_points"] or entity_count != row["entity_points"]:
        raise RuntimeError("Qdrant/PostgreSQL projection counts differ")
    if aliases.get("raise_evidence_active") != row["evidence_collection"] or aliases.get("raise_entities_active") != row["entity_collection"]:
        raise RuntimeError("Qdrant active aliases differ from PostgreSQL release")

    pool = ConnectionPool(database_url, min_size=1, max_size=3, kwargs={"row_factory": dict_row})
    service = QdrantGraphRetrieval(
        GraphRepository(pool.connection),
        QdrantProjectionRepository(pool.connection),
        _NoFallback(),
        config=config,
    )
    probes = []
    try:
        for request in (
            RetrievalRequest(query="potato irrigation soil", language="en", mode="quick", top_k=5),
            RetrievalRequest(query="سلامة المبيدات والآفات", language="ar", mode="standard", top_k=5),
            RetrievalRequest(query="compare soil water cost and risk", language="en", mode="deep", graph_hops=2, top_k=5),
        ):
            bundle = await service.retrieve(request)
            if not bundle.passages or bundle.release_id != row["release_id"]:
                raise RuntimeError("retrieval smoke probe returned no exact-release evidence")
            probes.append(
                {
                    "route": bundle.retrieval_route,
                    "passages": len(bundle.passages),
                    "claims": len(bundle.claims),
                    "paths": len(bundle.graph_paths),
                }
            )
    finally:
        await service.close()
        pool.close()
    return {
        "status": "ok",
        "revision": revision,
        "release_id": row["release_id"],
        "evidence_points": evidence_count,
        "entity_points": entity_count,
        "agreement": agreement_check,
        "probes": probes,
    }


def _check_legal_api(api_url: str) -> dict[str, int]:
    lengths: dict[str, int] = {}
    for language in ("en", "ar"):
        with urlopen(
            f"{api_url}/v1/legal/agreement?language={language}", timeout=5
        ) as response:
            payload = json.load(response)
        markdown = payload.get("markdown", "")
        if not isinstance(markdown, str) or len(markdown.strip()) < 500:
            raise RuntimeError(f"{language} user agreement is missing or incomplete")
        lengths[language] = len(markdown)
    return lengths

def main() -> None:
    print(json.dumps(asyncio.run(run()), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
