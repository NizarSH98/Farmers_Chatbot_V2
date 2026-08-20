
import pytest

from farmers_chatbot.knowledge import SearchResult
from farmers_chatbot.release_knowledge import KnowledgeSearch, ReleaseUnavailable


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
        match: str = "exact",
    ) -> None:
        self.results = results if results is not None else [_default_result()]
        self.sources = sources or {"source-1": {"id": "source-1", "title": "Source"}}
        self.available = available
        self.match = match

    def _guard(self) -> None:
        if not self.available:
            raise ReleaseUnavailable("no active release in this test")

    def search(
        self,
        query: str,
        *,
        language: str,
        top_k: int = 5,
    ) -> KnowledgeSearch:
        self._guard()
        return KnowledgeSearch(results=self.results[:top_k], match=self.match)

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
def store():
    """Evidence/quota persistence, which is now the same PostgreSQL store."""

    created = new_pilot_store()
    try:
        yield created
    finally:
        created.close()


# --- PostgreSQL-backed fixtures -------------------------------------------
# Anything whose behaviour depends on the database is tested against the real
# Compose PostgreSQL, not a double. A gateway that only talks to a database
# cannot be verified by something that is not a database.

import os
import subprocess
import sys

import pytest as _pytest

DEFAULT_TEST_DSN = "postgresql://raise:raise-local-only@127.0.0.1:55432/raise_test"
_TRUNCATE = """
TRUNCATE users, projects, conversations, messages, documents, document_chunks,
         artifacts, feedback, query_events, uploads, assistant_turns,
         provider_calls, whatsapp_events
RESTART IDENTITY CASCADE
"""
_READY: dict[str, str] = {}


def test_database_url() -> str:
    return os.getenv("TEST_DATABASE_URL", DEFAULT_TEST_DSN)


def _prepare(dsn: str) -> str:
    """Create the throwaway test database once per session and migrate it."""

    import psycopg

    head, _, database = dsn.rpartition("/")
    try:
        with psycopg.connect(
            f"{head}/postgres", connect_timeout=8, autocommit=True
        ) as admin:
            if not admin.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s", (database,)
            ).fetchone():
                admin.execute(f'CREATE DATABASE "{database}"')
    except psycopg.OperationalError as exc:
        _pytest.skip(f"local PostgreSQL is unavailable: {exc}")
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        env={**os.environ, "DATABASE_URL": dsn},
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        _pytest.skip(f"could not migrate the test database: {result.stderr[-400:]}")
    return dsn


def new_pilot_store():
    """Return a PilotStore on an empty test database.

    Used instead of a fixture so migrating call sites needs no signature change.
    """

    from farmers_chatbot.pilot_store import PilotStore

    dsn = _READY.get("dsn") or _prepare(test_database_url())
    _READY["dsn"] = dsn
    store = PilotStore(database_url=dsn)
    with store._connect() as connection:
        connection.execute(_TRUNCATE)
    return store


@_pytest.fixture()
def pilot_store():
    store = new_pilot_store()
    try:
        yield store
    finally:
        store.close()
