from app.ingestion.services.ingestion_service import IngestionService
from app.models.company import Company
from app.models.market import MarketData


def test_ingest():

    service = IngestionService()

    result = service.ingest(
        ticker="AAPL",
        filing_limit=2,
    )

    assert isinstance(result, dict)

    assert "company" in result
    assert "market" in result
    assert "filings" in result

    assert isinstance(result["company"], Company)
    assert isinstance(result["market"], MarketData)

    assert len(result["filings"]) <= 2