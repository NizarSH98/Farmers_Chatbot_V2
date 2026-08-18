from farmers_chatbot.qdrant_retrieval import QdrantGraphRetrieval
from farmers_chatbot.retrieval import RetrievalRequest


def test_arabizi_detection_is_language_scoped() -> None:
    arabizi = RetrievalRequest(
        query="kif fine 2allel may w shu lezim e3mel?",
        language="ar",
        mode="standard",
    )
    english = RetrievalRequest(
        query="how can I reduce water?",
        language="en",
        mode="standard",
    )
    assert QdrantGraphRetrieval._likely_arabizi(arabizi)
    assert not QdrantGraphRetrieval._likely_arabizi(english)
