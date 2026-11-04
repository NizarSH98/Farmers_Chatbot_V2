"""Startup warm-up loads embedding models once and never blocks or breaks the API."""

from __future__ import annotations

import threading
import time
from types import SimpleNamespace

import pytest

from farmers_chatbot.qdrant_projection import LocalEmbeddingService, ProjectionConfig
from farmers_chatbot.retrieval import RetrievalService
from farmers_chatbot.web_api import _warm_retrieval


def _config() -> ProjectionConfig:
    return ProjectionConfig(
        url="http://unused:6333",
        api_key=None,
        embedding_model="intfloat/multilingual-e5-small",
        embedding_dimensions=384,
        cache_dir="model-cache",
    )


def test_concurrent_first_use_loads_the_dense_model_once(monkeypatch):
    service = LocalEmbeddingService(_config())
    loads: list[int] = []

    def slow_load():
        loads.append(1)
        time.sleep(0.05)
        return object()

    monkeypatch.setattr(service, "_load_dense_model", slow_load)
    results: list[object] = []
    threads = [threading.Thread(target=lambda: results.append(service._dense_model())) for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(loads) == 1
    assert len({id(item) for item in results}) == 1


class _Retrieval:
    def __init__(self, outcome):
        self.outcome = outcome
        self.calls = 0

    async def warm_up(self):
        self.calls += 1
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return self.outcome


@pytest.mark.asyncio
async def test_warm_up_time_is_reported_for_health(monkeypatch):
    monkeypatch.setenv("RAG_WARM_UP", "true")
    app = SimpleNamespace(state=SimpleNamespace())
    await _warm_retrieval(app, _Retrieval(1.2345))
    assert app.state.retrieval_warm_seconds == 1.23


@pytest.mark.asyncio
async def test_failed_warm_up_is_logged_not_raised(monkeypatch, caplog):
    monkeypatch.setenv("RAG_WARM_UP", "true")
    app = SimpleNamespace(state=SimpleNamespace())
    await _warm_retrieval(app, _Retrieval(RuntimeError("model download blocked")))
    assert app.state.retrieval_warm_seconds is None
    assert "warm-up failed" in caplog.text


@pytest.mark.asyncio
async def test_warm_up_can_be_disabled_and_tolerates_no_retrieval(monkeypatch):
    monkeypatch.setenv("RAG_WARM_UP", "false")
    retrieval = _Retrieval(1.0)
    app = SimpleNamespace(state=SimpleNamespace())
    await _warm_retrieval(app, retrieval)
    assert retrieval.calls == 0

    monkeypatch.setenv("RAG_WARM_UP", "true")
    await _warm_retrieval(app, None)
    assert app.state.retrieval_warm_seconds is None


@pytest.mark.asyncio
async def test_base_retrieval_has_nothing_to_warm():
    assert await RetrievalService().warm_up() is None
