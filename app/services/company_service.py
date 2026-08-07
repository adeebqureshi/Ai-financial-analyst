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
from app.ingestion.services.sec_service import SECService
from app.schemas.responses import CompanyData

logger = get_logger(__name__)


class CompanyService:
    """
    Service for retrieving company profile information.

    Attributes:
        _settings: Application settings instance.
        _sec: SEC EDGAR service for company data.
    """

    def __init__(self, settings: Settings) -> None:
        """
        Initialize the company service.

        Args:
            settings: The application settings instance.
        """
        self._settings = settings
        self._sec = SECService()

    def get_company(self, ticker: str) -> CompanyData:
        """
        Retrieve company profile by ticker.

        Args:
            ticker: The ticker symbol (e.g., ``"AAPL"``).

        Returns:
            A ``CompanyData`` with the company profile.
        """
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
        except Exception as exc:
            logger.warning("Failed to retrieve company data for %s: %s", ticker, exc)
            return CompanyData(
                ticker=ticker,
                name=ticker,
            )