"""Benchmark bilingual OpenRouter embeddings without silently enabling vectors."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import math
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from farmers_chatbot.provider import ProviderClient
from scripts.evaluation.metrics import mean, percentile, retrieval_score, rounded
from scripts.evaluation.schema import EvaluationCase, load_cases

SCHEMA_VERSION = "raise.embedding_benchmark.v1"


@dataclass(frozen=True)
class Candidate:
    model: str
    dimensions: int
    stability: str
    input_cost_per_token_usd: float

    @property
    def candidate_id(self) -> str:
        return f"{self.model}@{self.dimensions}"


@dataclass(frozen=True)
class CorpusItem:
    evidence_id: str
    text: str
    language: str


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_candidates(path: Path) -> tuple[Candidate, ...]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("schema_version") != "raise.embedding_candidates.v1":
        raise ValueError("Unsupported embedding candidate manifest")
    candidates = tuple(Candidate(**item) for item in raw.get("candidates") or [])
    if not candidates:
        raise ValueError("Embedding candidate manifest is empty")
    if len({item.candidate_id for item in candidates}) != len(candidates):
        raise ValueError("Embedding candidate IDs must be unique")
    return candidates


def _load_corpus(path: Path) -> tuple[CorpusItem, ...]:
    items: list[CorpusItem] = []
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        raw = json.loads(line)
        try:
            item = CorpusItem(
                evidence_id=str(raw["evidence_id"]).strip(),
                text=str(raw["text"]).strip(),
                language=str(raw.get("language") or "unknown").strip(),
            )
        except KeyError as exc:
            raise ValueError(f"Corpus line {line_number} is missing {exc.args[0]}") from exc
        if not item.evidence_id or not item.text:
            raise ValueError(f"Corpus line {line_number} has an empty required field")
        items.append(item)
    if not items or len({item.evidence_id for item in items}) != len(items):
        raise ValueError("Corpus must be non-empty with unique evidence IDs")
    return tuple(items)


def _cosine(left: list[float], right: list[float]) -> float:
    numerator = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if not left_norm or not right_norm:
        return 0.0
    return numerator / (left_norm * right_norm)


def select_candidate(results: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Apply the pre-registered quality, parity, latency, and cost gate."""

    scored = [item for item in results if item.get("ndcg_at_10") is not None]
    if not scored:
        return None
    best_ndcg = max(float(item["ndcg_at_10"]) for item in scored)
    eligible = [
        item
        for item in scored
        if float(item.get("recall_at_10") or 0) >= 0.90
        and float(item.get("language_gap") or 1) < 0.05
        and float(item.get("retrieval_p95_ms") or math.inf) < 300
        and float(item["ndcg_at_10"]) >= best_ndcg - 0.01
    ]
    if not eligible:
        return None
    return min(
        eligible,
        key=lambda item: (
            float(item.get("estimated_cost_usd") or 0),
            -float(item["ndcg_at_10"]),
            str(item["candidate_id"]),
        ),
    )


async def _benchmark_candidate(
    provider: ProviderClient,
    candidate: Candidate,
    cases: tuple[EvaluationCase, ...],
    corpus: tuple[CorpusItem, ...],
) -> dict[str, Any]:
    record_start = len(provider.records)
    document_response = await provider.embed(
        stage=f"embedding_benchmark_documents:{candidate.candidate_id}",
        inputs=[item.text for item in corpus],
        model=candidate.model,
        dimensions=candidate.dimensions,
        input_type="search_document",
    )
    scores = []
    latency_ms: list[float] = []
    by_language: dict[str, list[float]] = {"arabic": [], "english": []}
    for case in cases:
        started = time.perf_counter()
        query_response = await provider.embed(
            stage=f"embedding_benchmark_query:{candidate.candidate_id}",
            inputs=[case.prompt],
            model=candidate.model,
            dimensions=candidate.dimensions,
            input_type="search_query",
        )
        ranked = sorted(
            zip(corpus, document_response.embeddings, strict=True),
            key=lambda item: _cosine(query_response.embeddings[0], item[1]),
            reverse=True,
        )
        latency_ms.append((time.perf_counter() - started) * 1000)
        relevance = {
            item.evidence_id: item.relevance for item in case.relevant_evidence
        }
        score = retrieval_score(
            [item[0].evidence_id for item in ranked], relevance, top_k=10
        )
        scores.append(score)
        if score.ndcg is not None and case.language_group in by_language:
            by_language[case.language_group].append(score.ndcg)

    arabic = mean(by_language["arabic"])
    english = mean(by_language["english"])
    records = provider.records[record_start:]
    prompt_tokens = sum(
        record.usage.prompt_tokens or 0 for record in records
    )
    cost = prompt_tokens * candidate.input_cost_per_token_usd
    return {
        "candidate_id": candidate.candidate_id,
        "model": candidate.model,
        "dimensions": candidate.dimensions,
        "stability": candidate.stability,
        "case_count": len(cases),
        "recall_at_10": rounded(
            mean(score.recall for score in scores if score.recall is not None)
        ),
        "ndcg_at_10": rounded(
            mean(score.ndcg for score in scores if score.ndcg is not None)
        ),
        "arabic_ndcg_at_10": rounded(arabic),
        "english_ndcg_at_10": rounded(english),
        "language_gap": rounded(
            None if arabic is None or english is None else abs(arabic - english)
        ),
        "retrieval_p95_ms": rounded(percentile(latency_ms, 0.95)),
        "prompt_tokens": prompt_tokens,
        "estimated_cost_usd": rounded(cost),
    }


async def run(args: argparse.Namespace) -> dict[str, Any]:
    cases = tuple(case for case in load_cases(args.cases) if not case.fixture_only)
    corpus = _load_corpus(args.corpus)
    evidence_ids = {item.evidence_id for item in corpus}
    missing = sorted(
        {
            evidence.evidence_id
            for case in cases
            for evidence in case.relevant_evidence
            if evidence.evidence_id not in evidence_ids
        }
    )
    if not cases:
        raise ValueError("Embedding benchmark requires non-fixture evaluation cases")
    if missing:
        raise ValueError(f"Relevant evidence missing from corpus: {', '.join(missing)}")
    candidates = _load_candidates(args.candidates)
    provider = ProviderClient(api_key=os.getenv("OPENROUTER_API_KEY", ""))
    if not provider.configured:
        await provider.close()
        raise RuntimeError("OPENROUTER_API_KEY is required for the embedding benchmark")
    try:
        results = [
            await _benchmark_candidate(provider, candidate, cases, corpus)
            for candidate in candidates
        ]
    finally:
        await provider.close()
    selected = select_candidate(results)
    return {
        "schema_version": SCHEMA_VERSION,
        "cases_sha256": _sha256(args.cases),
        "corpus_sha256": _sha256(args.corpus),
        "candidates_sha256": _sha256(args.candidates),
        "criteria": {
            "recall_at_10_min": 0.90,
            "within_best_ndcg_points": 0.01,
            "language_gap_max_exclusive": 0.05,
            "retrieval_p95_ms_max_exclusive": 300,
            "selection": "lowest estimated cost among eligible candidates",
        },
        "results": results,
        "selected": selected["candidate_id"] if selected else None,
        "vector_cutover_allowed": selected is not None,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument(
        "--candidates",
        type=Path,
        default=Path("evaluation/embedding_candidates.v1.json"),
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = asyncio.run(run(args))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"output": str(args.output), "selected": report["selected"]}))


if __name__ == "__main__":
    main()
