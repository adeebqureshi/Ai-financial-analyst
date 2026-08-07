from datetime import date

from app.retrieval.filters import MetadataFilter
from app.retrieval.models import RetrievedChunk


def make_chunk(
    ticker: str,
    filing: str,
    year: int,
):

    return RetrievedChunk(
        id=f"{ticker}-{year}",
        text="Sample",
        score=1.0,
        ticker=ticker,
        filing_type=filing,
        filing_date=date(year, 1, 1),
        section="MD&A",
        source="SEC",
    )


def test_filter_ticker():

    chunks = [
        make_chunk("AAPL", "10-K", 2024),
        make_chunk("MSFT", "10-K", 2024),
    ]

    results = MetadataFilter().filter(
        chunks,
        ticker="AAPL",
    )

    assert len(results) == 1
    assert results[0].ticker == "AAPL"


def test_filter_year():

    chunks = [
        make_chunk("AAPL", "10-K", 2023),
        make_chunk("AAPL", "10-K", 2024),
    ]

    results = MetadataFilter().filter(
        chunks,
        year=2024,
    )

    assert len(results) == 1
    assert results[0].filing_date.year == 2024


def test_filter_filing():

    chunks = [
        make_chunk("AAPL", "10-K", 2024),
        make_chunk("AAPL", "10-Q", 2024),
    ]

    results = MetadataFilter().filter(
        chunks,
        filing_type="10-Q",
    )

    assert len(results) == 1
    assert results[0].filing_type == "10-Q"