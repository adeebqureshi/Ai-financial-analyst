from datetime import date

from app.retrieval.models import RetrievedChunk
from app.retrieval.models import RetrievalContext


def test_retrieved_chunk():

    chunk = RetrievedChunk(
        id="1",
        text="Revenue increased.",
        score=0.9,
        ticker="AAPL",
        filing_type="10-K",
        filing_date=date(2024, 10, 31),
        section="MD&A",
        source="SEC",
    )

    assert chunk.ticker == "AAPL"


def test_context():

    context = RetrievalContext(
        query="Revenue",
        chunks=[],
        retrieval_time_ms=18,
    )

    assert context.query == "Revenue"