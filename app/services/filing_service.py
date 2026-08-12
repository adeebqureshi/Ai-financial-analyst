"""
Filing Service

This module contains the business logic for retrieving and managing SEC filings.
It delegates to the existing ``SECService`` for data retrieval and wraps the
results in typed response DTOs.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from app.core.config import Settings
from app.core.logging import get_logger
from app.enums.filing_type import FilingType
from app.ingestion.services.sec_service import SECService
from app.models.filing import Filing

logger = get_logger(__name__)


class FilingService:
    """
    Service for retrieving and managing SEC filings.

    Attributes:
        _settings: Application settings instance.
        _sec: SEC EDGAR service for filing data.
    """

    def __init__(self, settings: Settings) -> None:
        """
        Initialize the filing service.

        Args:
            settings: The application settings instance.
        """
        self._settings = settings
        self._sec = SECService()

    def get_latest_filings(
        self,
        ticker: str,
        filing_type: FilingType | str = FilingType.FORM_10K,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Retrieve latest SEC filings for a company.

        Args:
            ticker: The ticker symbol (e.g., "AAPL").
            filing_type: The type of filing to retrieve (default: 10-K).
            limit: Maximum number of filings to return.

        Returns:
            A list of filing records.
        """
        ticker = ticker.upper()
        form = filing_type.value if isinstance(filing_type, FilingType) else filing_type

        try:
            filings = self._sec.get_latest_filings(
                ticker=ticker,
                form=form,
                limit=limit,
            )
            return self._normalize_filings(filings)
        except Exception as exc:
            logger.warning(
                "Failed to retrieve filings for %s: %s",
                ticker,
                exc,
            )
            return []

    def get_filing_by_accession(
        self,
        ticker: str,
        accession_number: str,
    ) -> dict[str, Any] | None:
        """
        Retrieve a specific filing by accession number.

        Args:
            ticker: The ticker symbol.
            accession_number: The SEC accession number.

        Returns:
            The filing record if found, None otherwise.
        """
        ticker = ticker.upper()
        filings = self.get_latest_filings(ticker, limit=100)
        for filing in filings:
            if filing.get("accession_number") == accession_number:
                return filing
        return None

    def get_filings_by_date_range(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
        filing_type: FilingType | str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Retrieve filings within a date range.

        Args:
            ticker: The ticker symbol.
            start_date: Start date (inclusive).
            end_date: End date (inclusive).
            filing_type: Optional filing type filter.

        Returns:
            A list of filing records within the date range.
        """
        filings = self.get_latest_filings(ticker, limit=100)
        form = filing_type.value if isinstance(filing_type, FilingType) else filing_type

        filtered = []
        for filing in filings:
            filing_date = filing.get("filing_date")
            if isinstance(filing_date, str):
                filing_date = date.fromisoformat(filing_date)
            if start_date <= filing_date <= end_date:
                if form is None or filing.get("filing_type") == form:
                    filtered.append(filing)
        return filtered

    def _normalize_filings(self, filings: Any) -> list[dict[str, Any]]:
        """
        Normalize filing data from the SEC client to a consistent format.

        Args:
            filings: Raw filing data from SEC client.

        Returns:
            A list of normalized filing dictionaries.
        """
        normalized = []
        for filing in filings:
            if hasattr(filing, "model_dump"):
                filing_dict = filing.model_dump()
            elif hasattr(filing, "dict"):
                filing_dict = filing.dict()
            else:
                filing_dict = filing

            normalized.append({
                "accession_number": filing_dict.get("accession_number", ""),
                "filing_type": filing_dict.get("filing_type", ""),
                "filing_date": filing_dict.get("filing_date"),
                "report_period": filing_dict.get("report_period"),
                "source_url": filing_dict.get("source_url", ""),
                "local_path": str(filing_dict.get("local_path", "")),
                "checksum": filing_dict.get("checksum"),
                "parser_status": filing_dict.get("parser_status", "pending"),
                "embedding_status": filing_dict.get("embedding_status", "pending"),
                "indexing_status": filing_dict.get("indexing_status", "pending"),
            })
        return normalized