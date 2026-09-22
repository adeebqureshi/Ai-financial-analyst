from __future__ import annotations
from app.ingestion.services.market_service import MarketService
from app.ingestion.services.sec_service import SECService
class IngestionService:
    def __init__(self) -> None:
        self.sec_service = SECService()
        self.market_service = MarketService()
    def ingest(
        self,
        ticker: str,
        filing_form: str = "10-K",
        filing_limit: int = 5,
    ) -> dict:
        company = self.sec_service.get_company(ticker)
        market = self.market_service.get_market_data(ticker)
        filings = self.sec_service.get_latest_filings(
            ticker=ticker,
            form=filing_form,
            limit=filing_limit,
        )
        return {
            "company": company,
            "market": market,
            "filings": filings,
        }