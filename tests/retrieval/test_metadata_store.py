from datetime import date

from app.retrieval.metadata_store import MetadataStore
from app.retrieval.models import RetrievedChunk


def test_metadata_store():

    store = MetadataStore()

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

    store.add(chunk)

    result = store.get("1")

    assert result.ticker == "AAPL"


def test_add_many():

    store = MetadataStore()

    chunks = [
        RetrievedChunk(
            id="1",
            text="A",
            score=1,
            ticker="AAPL",
            filing_type="10-K",
            filing_date=None,
            section="Risk",
            source="SEC",
        ),
        RetrievedChunk(
            id="2",
            text="B",
            score=1,
            ticker="MSFT",
            filing_type="10-K",
            filing_date=None,
            section="Risk",
            source="SEC",
        ),
    ]

    store.add_many(chunks)

    results = store.get_many(["1", "2"])

    assert len(results) == 2