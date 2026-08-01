from pathlib import Path

import pytest

from farmers_chatbot.knowledge import KnowledgeIndex
from farmers_chatbot.storage import EvidenceStore


@pytest.fixture(scope="session")
def knowledge() -> KnowledgeIndex:
    return KnowledgeIndex.from_directory()


@pytest.fixture()
def store(tmp_path: Path) -> EvidenceStore:
    return EvidenceStore(tmp_path / "runtime.sqlite3")

