from pathlib import Path

import pytest

from farmers_chatbot.knowledge import SearchResult
from farmers_chatbot.release_knowledge import ReleaseUnavailable
from farmers_chatbot.storage import EvidenceStore


class FakeReleaseKnowledge:
    """In-memory stand-in for `ReleaseKnowledgeGateway`.

    Release-backed lookup needs PostgreSQL, so unit tests that only need *a*
    knowledge surface use this. Tests that need real release semantics run
    against the Compose database.
    """

    def __init__(
        self,
        results: list[SearchResult] | None = None,
        sources: dict[str, dict] | None = None,
        *,
        available: bool = True,
    ) -> None:
        self.results = results if results is not None else [_default_result()]
        self.sources = sources or {"source-1": {"id": "source-1", "title": "Source"}}
        self.available = available

    def _guard(self) -> None:
        if not self.available:
            raise ReleaseUnavailable("no active release in this test")

    def search(
        self,
        query: str,
        *,
        language: str,
        top_k: int = 5,
    ) -> list[SearchResult]:
        self._guard()
        return self.results[:top_k]

    def get_source(self, source_id: str) -> dict | None:
        self._guard()
        return self.sources.get(source_id)


def _default_result() -> SearchResult:
    return SearchResult(
        item_id="chunk-1",
        title="Tomato pest control",
        text="Inspect tomato plants before selecting pest controls.",
        language="english",
        geography=("Akkar",),
        topics=(),
        source_ids=("source-1",),
        evidence_class="guidance",
        risk="medium",
        status="approved",
        score=0.9,
    )


@pytest.fixture(scope="session")
def knowledge() -> FakeReleaseKnowledge:
    return FakeReleaseKnowledge()


@pytest.fixture()
def store(tmp_path: Path) -> EvidenceStore:
    return EvidenceStore(tmp_path / "runtime.sqlite3")
