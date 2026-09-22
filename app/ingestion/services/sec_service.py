from __future__ import annotations
import logging
from app.enums.exchange import Exchange
from app.ingestion.clients.edgar_client import EdgarClient
from app.ingestion.mappers.company_mapper import CompanyMapper
from app.models.company import Company
from app.utils.tickers import normalize_ticker
logger = logging.getLogger(__name__)
class SECService:
    def __init__(self) -> None:
        self.client = EdgarClient()
    def get_company(self, ticker: str):
        ticker = normalize_ticker(ticker)
        try:
            company = self.client.get_company(ticker)
            return CompanyMapper.from_edgar(company)
        except Exception as exc:
            logger.warning(
                "Could not fetch company %s from EDGAR: %s. "
                "Returning stub company. Set EDGAR_IDENTITY in .env to enable SEC data.",
                ticker,
                exc,
            )
            return Company(
                ticker=ticker,
                cik="0",
                name=ticker,
                exchange=Exchange.NASDAQ,
                sector="Unknown",
                industry="Unknown",
                country="USA",
                currency="USD",
                website=None,
                market_cap=None,
            )
    def get_latest_filings(
        self,
        ticker: str,
        form: str = "10-K",
        limit: int = 5,
    ):
        ticker = normalize_ticker(ticker)
        return self.client.get_filings(
            ticker=ticker,
            form=form,
            limit=limit,
        )