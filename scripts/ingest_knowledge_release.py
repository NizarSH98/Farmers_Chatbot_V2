"""Validate or ingest one immutable canonical Markdown knowledge release."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
from dataclasses import asdict
from pathlib import Path

from farmers_chatbot.embedding_approval import (
    EmbeddingApprovalError,
    load_embedding_approval,
)
from farmers_chatbot.embedding_ingestion import populate_release_embeddings
from farmers_chatbot.graph_repository import GraphRepository
from farmers_chatbot.knowledge_release import PARSER_VERSION, build_release_batch
from farmers_chatbot.provider import ProviderClient


def _approval(args: argparse.Namespace) -> dict[str, object] | None:
    if args.embedding_model == "lexical-only":
        return None
    if not args.embedding_report or not args.embedding_report_sha256:
        raise SystemExit(
            "Vector ingestion requires --embedding-report and "
            "--embedding-report-sha256"
        )
    try:
        approval = load_embedding_approval(
            args.embedding_report,
            expected_sha256=args.embedding_report_sha256,
        )
    except EmbeddingApprovalError as exc:
        raise SystemExit(f"Embedding benchmark approval is invalid: {exc}") from exc
    if (
        approval.model != args.embedding_model
        or approval.dimensions != args.embedding_dimensions
    ):
        raise SystemExit(
            "Requested embedding model/dimensions do not match the approved report"
        )
    return asdict(approval)


async def _run(args: argparse.Namespace) -> None:
    approval = _approval(args)
    if args.activate == "production":
        raise SystemExit("An ai_draft corpus cannot be activated for production")
    batch = build_release_batch(
        args.input,
        embedding_model=args.embedding_model,
        embedding_dimensions=args.embedding_dimensions,
        embedding_approval=approval,
        created_by=args.activated_by,
    )
    summary: dict[str, object] = {
        "release_id": batch.release.id,
        "sources": len(batch.sources),
        "documents": len(batch.documents),
        "chunks": len(batch.chunks),
        "entities": len(batch.entities),
        "claims": len(batch.claims),
        "relations": len(batch.relations),
        "evidence": len(batch.evidence),
        "embedding_approval": approval,
    }
    if args.validate_only:
        print(
            json.dumps(
                {
                    **summary,
                    "validated": True,
                    "embedding_population_required": approval is not None,
                },
                sort_keys=True,
            )
        )
        return
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url.startswith(("postgres://", "postgresql://")):
        raise SystemExit("A PostgreSQL DATABASE_URL is required for ingestion")
    try:
        from psycopg.rows import dict_row
        from psycopg_pool import ConnectionPool
    except ImportError as exc:
        raise SystemExit(
            "psycopg and psycopg-pool are required for ingestion"
        ) from exc
    pool = ConnectionPool(
        database_url,
        min_size=1,
        max_size=2,
        kwargs={"row_factory": dict_row},
    )
    provider: ProviderClient | None = None
    try:
        repository = GraphRepository(pool.connection)
        if approval is not None:
            provider = ProviderClient(api_key=os.getenv("OPENROUTER_API_KEY", ""))
            if not provider.configured:
                raise SystemExit(
                    "OPENROUTER_API_KEY is required for approved vector ingestion"
                )
            population = await populate_release_embeddings(
                batch,
                provider=provider,
                cache=repository,
                batch_size=args.embedding_batch_size,
            )
            batch = population.batch
            summary["embedding_population"] = {
                "total_chunks": population.total_chunks,
                "unique_inputs": population.unique_inputs,
                "cache_hits": population.cache_hits,
                "provider_inputs": population.provider_inputs,
            }
        repository.create_release(batch.release)
        input_hash = hashlib.sha256(args.input.read_bytes()).hexdigest()
        run = repository.begin_ingestion(
            batch.release.id,
            input_hash,
            parser_version=PARSER_VERSION,
        )
        if run["state"] != "completed":
            try:
                stats: dict[str, object] = repository.ingest_batch(batch)
                if "embedding_population" in summary:
                    stats["embedding_population"] = summary["embedding_population"]
                repository.complete_ingestion(str(run["id"]), stats=stats)
            except Exception as exc:
                repository.complete_ingestion(
                    str(run["id"]),
                    stats={},
                    error_type=type(exc).__name__,
                )
                raise
        counts = repository.seal_release(batch.release.id)
        activation = None
        if args.activate:
            activation = asdict(
                repository.activate_release(
                    args.activate,
                    batch.release.id,
                    activated_by=args.activated_by,
                )
            )
        print(
            json.dumps(
                {**summary, "sealed": counts, "activation": activation},
                sort_keys=True,
            )
        )
    finally:
        if provider is not None:
            await provider.close()
        pool.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("knowledge_base/agrifood_knowledge_draft_v0.2.md"),
    )
    parser.add_argument("--embedding-model", default="lexical-only")
    parser.add_argument("--embedding-dimensions", type=int, default=768)
    parser.add_argument("--embedding-report", type=Path)
    parser.add_argument("--embedding-report-sha256")
    parser.add_argument("--embedding-batch-size", type=int, default=64)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--activate", choices=("pilot", "production"))
    parser.add_argument("--activated-by")
    args = parser.parse_args()
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
