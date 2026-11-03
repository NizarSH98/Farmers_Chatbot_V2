"""Embedding approval and resumable release population regressions."""

from __future__ import annotations

import json
from dataclasses import replace

import pytest

from farmers_chatbot.embedding_approval import (
    EmbeddingApprovalError,
    load_embedding_approval,
)
from farmers_chatbot.embedding_ingestion import populate_release_embeddings
from farmers_chatbot.knowledge_release import build_release_batch
from farmers_chatbot.provider import EmbeddingResponse, ProviderUsage


def _report() -> dict[str, object]:
    digest = "a" * 64
    return {
        "schema_version": "raise.embedding_benchmark.v1",
        "cases_sha256": digest,
        "corpus_sha256": digest,
        "candidates_sha256": digest,
        "vector_cutover_allowed": True,
        "selected": "approved/model@768",
        "results": [
            {
                "candidate_id": "approved/model@768",
                "model": "approved/model",
                "dimensions": 768,
                "recall_at_10": 0.91,
                "ndcg_at_10": 0.82,
                "language_gap": 0.03,
                "retrieval_p95_ms": 120,
                "estimated_cost_usd": 0.01,
            }
        ],
    }


def test_embedding_approval_recomputes_hard_gates(tmp_path) -> None:
    path = tmp_path / "report.json"
    path.write_text(json.dumps(_report()), encoding="utf-8")
    approval = load_embedding_approval(path)
    assert approval.model == "approved/model"
    assert approval.dimensions == 768

    failed = _report()
    failed["results"][0]["language_gap"] = 0.05  # type: ignore[index]
    path.write_text(json.dumps(failed), encoding="utf-8")
    with pytest.raises(EmbeddingApprovalError, match="hard gate"):
        load_embedding_approval(path)


class _Cache:
    def __init__(self) -> None:
        self.values: dict[str, tuple[float, ...]] = {}

    def cached_embeddings(self, **kwargs):
        return {
            digest: self.values[digest]
            for digest in kwargs["content_hashes"]
            if digest in self.values
        }

    def cache_embeddings(self, **kwargs):
        self.values.update(kwargs["embeddings"])
        return len(kwargs["embeddings"])


class _Provider:
    def __init__(self) -> None:
        self.inputs = 0

    async def embed(self, **kwargs):
        self.inputs += len(kwargs["inputs"])
        return EmbeddingResponse(
            embeddings=[
                [float(index + 1)] * kwargs["dimensions"]
                for index, _ in enumerate(kwargs["inputs"])
            ],
            usage=ProviderUsage(),
            model=kwargs["model"],
            raw={},
        )


@pytest.mark.asyncio
async def test_release_embeddings_are_batched_cached_and_reusable() -> None:
    source = build_release_batch(
        "knowledge_base/agrifood_knowledge_v0.3.en.md",
        embedding_model="approved/model",
        embedding_dimensions=768,
    )
    repeated = replace(source, chunks=(*source.chunks, source.chunks[0]))
    repeated = replace(
        repeated,
        chunks=tuple(
            replace(chunk, id=f"{chunk.id}-{index}")
            for index, chunk in enumerate(repeated.chunks)
        ),
        evidence=(),
        claims=(),
        relations=(),
    )
    cache = _Cache()
    provider = _Provider()
    first = await populate_release_embeddings(  # type: ignore[arg-type]
        repeated, provider=provider, cache=cache, batch_size=7
    )
    assert first.provider_inputs == first.unique_inputs
    assert first.unique_inputs < first.total_chunks
    assert all(len(chunk.embedding or ()) == 768 for chunk in first.batch.chunks)
    assert provider.inputs == first.unique_inputs

    second = await populate_release_embeddings(  # type: ignore[arg-type]
        repeated, provider=provider, cache=cache, batch_size=7
    )
    assert second.cache_hits == second.unique_inputs
    assert second.provider_inputs == 0
    assert provider.inputs == first.unique_inputs


def test_release_embedding_approval_rejects_wrong_checksum(tmp_path) -> None:
    path = tmp_path / "report.json"
    path.write_text(json.dumps(_report()), encoding="utf-8")
    with pytest.raises(EmbeddingApprovalError, match="checksum"):
        load_embedding_approval(path, expected_sha256="0" * 64)
