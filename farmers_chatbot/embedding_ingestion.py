"""Resumable, content-hash cached embedding population for graph releases."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Protocol

from .graph_ingestion import (
    IngestionBatch,
    content_sha256,
    validate_batch,
)
from .provider import ProviderClient


class EmbeddingCache(Protocol):
    def cached_embeddings(
        self,
        *,
        model: str,
        dimensions: int,
        input_type: str,
        content_hashes: Sequence[str],
    ) -> dict[str, tuple[float, ...]]: ...

    def cache_embeddings(
        self,
        *,
        model: str,
        dimensions: int,
        input_type: str,
        embeddings: Mapping[str, Sequence[float]],
    ) -> int: ...


@dataclass(frozen=True)
class EmbeddingPopulation:
    batch: IngestionBatch
    total_chunks: int
    unique_inputs: int
    cache_hits: int
    provider_inputs: int


async def populate_release_embeddings(
    batch: IngestionBatch,
    *,
    provider: ProviderClient,
    cache: EmbeddingCache,
    batch_size: int = 64,
) -> EmbeddingPopulation:
    """Attach one approved embedding configuration to every release chunk."""

    if batch.release.embedding_model == "lexical-only":
        return EmbeddingPopulation(
            batch=batch,
            total_chunks=len(batch.chunks),
            unique_inputs=0,
            cache_hits=0,
            provider_inputs=0,
        )
    if not 1 <= batch_size <= 64:
        raise ValueError("Embedding batch size must be between 1 and 64")
    by_hash: dict[str, str] = {}
    for chunk in batch.chunks:
        digest = content_sha256(chunk.contextualized_content)
        existing = by_hash.setdefault(digest, chunk.contextualized_content)
        if existing != chunk.contextualized_content:
            raise ValueError("Embedding content hash collision detected")

    model = batch.release.embedding_model
    dimensions = batch.release.embedding_dimensions
    hashes = tuple(by_hash)
    resolved = cache.cached_embeddings(
        model=model,
        dimensions=dimensions,
        input_type="search_document",
        content_hashes=hashes,
    )
    cache_hits = len(resolved)
    missing = [digest for digest in hashes if digest not in resolved]
    for start in range(0, len(missing), batch_size):
        batch_hashes = missing[start : start + batch_size]
        response = await provider.embed(
            stage=f"release_embedding:{batch.release.id}",
            inputs=[by_hash[digest] for digest in batch_hashes],
            model=model,
            dimensions=dimensions,
            input_type="search_document",
        )
        if response.model != model:
            raise ValueError(
                "Embedding provider returned a model different from the approved model"
            )
        additions: dict[str, tuple[float, ...]] = {}
        for digest, vector in zip(
            batch_hashes, response.embeddings, strict=True
        ):
            value = tuple(float(item) for item in vector)
            if len(value) != dimensions or not all(
                math.isfinite(item) for item in value
            ):
                raise ValueError("Embedding provider returned an invalid vector")
            additions[digest] = value
        cache.cache_embeddings(
            model=model,
            dimensions=dimensions,
            input_type="search_document",
            embeddings=additions,
        )
        resolved.update(additions)
    if set(resolved) != set(hashes):
        raise ValueError("Embedding population is incomplete")

    chunks = tuple(
        replace(
            chunk,
            embedding=resolved[content_sha256(chunk.contextualized_content)],
            metadata={
                **chunk.metadata,
                "embedding_input_sha256": content_sha256(
                    chunk.contextualized_content
                ),
                "embedding_input_type": "search_document",
            },
        )
        for chunk in batch.chunks
    )
    populated = replace(batch, chunks=chunks)
    validate_batch(populated)
    return EmbeddingPopulation(
        batch=populated,
        total_chunks=len(chunks),
        unique_inputs=len(hashes),
        cache_hits=cache_hits,
        provider_inputs=len(missing),
    )

