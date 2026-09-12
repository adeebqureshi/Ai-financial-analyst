"""
Company Service

This module contains the business logic for retrieving company profile
information. It delegates to the existing ``SECService`` for data retrieval
and wraps the results in typed response DTOs.

Design Decisions:
    - **Extends existing empty file**: The ``CompanyService`` class fills the
      existing ``app/services/company_service.py`` module rather than creating
      a parallel implementation.
    - **Settings injection**: Consistent with other services, the constructor
      accepts ``Settings`` for dependency injection and testability.
"""

from __future__ import annotations

from app.core.config import Settings
from app.core.logging import get_logger
from app.financial.data import FinancialDataService
from app.ingestion.services.sec_service import SECService
from app.schemas.responses import CompanyData
from app.utils.tickers import normalize_ticker

# Lazy import for demo services
_demo_financial_data_service = None
_demo_sec_service = None


def _get_demo_financial_data_service():
    global _demo_financial_data_service
    if _demo_financial_data_service is None:
        from app.demo.services.demo_financial_data import DemoFinancialDataService

        _demo_financial_data_service = DemoFinancialDataService()
    return _demo_financial_data_service


def _get_demo_sec_service():
    global _demo_sec_service
    if _demo_sec_service is None:
        from app.demo.services.demo_sec_service import DemoSECService

        _demo_sec_service = DemoSECService()
    return _demo_sec_service

logger = get_logger(__name__)


class CompanyService:
    """
    Service for retrieving company profile information.

    The profile (name, sector, industry, market cap, description) is fetched
    from the existing market-data provider (Yahoo) so the returned values
    always correspond to the requested company. SEC EDGAR is used as a
    fallback when the market provider is unavailable.

    Attributes:
        _settings: Application settings instance.
        _sec: SEC EDGAR service for company data.
        _financial_data: Financial data service for company profiles.
    """

    def __init__(self, settings: Settings) -> None:
        """
        Initialize the company service.

        Args:
            settings: The application settings instance.
        """
        self._settings = settings
        if settings.is_demo_mode:
            self._sec = _get_demo_sec_service()
            self._financial_data = _get_demo_financial_data_service()
        else:
            self._sec = SECService()
            self._financial_data = FinancialDataService()

    def get_company(self, ticker: str) -> CompanyData:
        """
        Retrieve company profile by ticker.

        Args:
            ticker: The ticker symbol (e.g., ``"AAPL"``).

        Returns:
            A ``CompanyData`` with the company profile.
        """
        ticker = normalize_ticker(ticker)

        try:
            data = self._financial_data.load(ticker)
            return CompanyData(
                ticker=ticker,
                name=data.name,
                sector=data.sector,
                industry=data.industry,
                market_cap=data.market_cap,
                description=data.description,
            )
        except Exception as exc:
            logger.warning(
                "Failed to retrieve market profile for %s: %s. "
                "Falling back to SEC.",
                ticker,
                exc,
            )
            try:
                company = self._sec.get_company(ticker)
                return CompanyData(
                    ticker=ticker,
                    name=getattr(company, "name", ticker),
                    sector=getattr(company, "sector", None),
                    industry=getattr(company, "industry", None),
                    market_cap=getattr(company, "market_cap", None),
                    description=getattr(company, "description", None),
                )
            except Exception as exc2:
                logger.warning("SEC fallback also failed for %s: %s", ticker, exc2)
                return CompanyData(
                    ticker=ticker,
                    name=ticker,
                )