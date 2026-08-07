from datetime import date
from unittest.mock import MagicMock
from unittest.mock import patch

from app.retrieval.models import RetrievedChunk
from app.retrieval.retrieval_engine import RetrievalEngine


@patch("app.retrieval.retrieval_engine.HybridRetriever")
@patch("app.retrieval.retrieval_engine.EmbeddingService")
def test_retrieve(
    mock_embedder,
    mock_retriever,
):

    embedder = MagicMock()
    embedder.embed_text.return_value = [0.1, 0.2]
    mock_embedder.return_value = embedder

    retriever = MagicMock()
    retriever.search.return_value = ["1"]
    mock_retriever.return_value = retriever

    engine = RetrievalEngine()

    chunk = RetrievedChunk(
        id="1",
        text="Apple revenue",
        score=1.0,
        ticker="AAPL",
        filing_type="10-K",
        filing_date=date(2024, 10, 31),
        section="MD&A",
        source="SEC",
    )

    engine.metadata.add(chunk)

    context = engine.retrieve(
        "Apple revenue"
    )

    assert context.query == "Apple revenue"

    assert len(context.chunks) == 1

    assert context.chunks[0].ticker == "AAPL"