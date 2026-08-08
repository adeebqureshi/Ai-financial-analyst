"""
sec_service.py

Business logic for SEC EDGAR.
"""

from __future__ import annotations

import logging

from app.enums.exchange import Exchange
from app.ingestion.clients.edgar_client import EdgarClient
from app.ingestion.mappers.company_mapper import CompanyMapper
from app.models.company import Company

logger = logging.getLogger(__name__)


class SECService:
    """
    Business layer for SEC operations.
    """

    def __init__(self) -> None:
        self.client = EdgarClient()

    def get_company(self, ticker: str):
        """
        Retrieve a company and map it to our domain model.
        Returns a stub Company if EDGAR is unavailable.
        """
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
                ticker=ticker.upper(),
                cik="0",
                name=ticker.upper(),
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
        """
        Retrieve latest SEC filings.
        """

        return self.client.get_filings(
            ticker=ticker,
            form=form,
            limit=limit,
        )