from app.ingestion.clients.edgar_client import EdgarClient


def test_get_company():

    client = EdgarClient()

    company = client.get_company("AAPL")

    assert company is not None


def test_get_filings():

    client = EdgarClient()

    filings = client.get_filings(
        ticker="AAPL",
        form="10-K",
        limit=2,
    )

    assert len(filings) <= 2