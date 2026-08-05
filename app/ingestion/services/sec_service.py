"""
sec_service.py

Business logic for SEC EDGAR.
"""

from __future__ import annotations

from app.ingestion.clients.edgar_client import EdgarClient
from app.ingestion.mappers.company_mapper import CompanyMapper


class SECService:
    """
    Business layer for SEC operations.
    """

    def __init__(self) -> None:
        self.client = EdgarClient()

    def get_company(self, ticker: str):
        """
        Retrieve a company and map it to our domain model.
        """

        company = self.client.get_company(ticker)

        return CompanyMapper.from_edgar(company)

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