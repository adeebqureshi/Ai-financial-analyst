"""
Demo SEC Service

Deterministic SEC filing service for demo mode.
Provides synthetic SEC filings for demo tickers.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from app.demo.fixtures.companies import DEMO_TICKERS, is_demo_ticker
from app.enums.filing_type import FilingType
from app.models.filing import Filing
from app.utils.tickers import normalize_ticker


# ──────────────────────────────────────────────────────────────────────────────
# Demo Filing Fixtures
# ──────────────────────────────────────────────────────────────────────────────

DEMO_FILINGS: dict[str, list[dict[str, Any]]] = {
    "AAPL": [
        {
            "accession_number": "0000320193-24-000123",
            "filing_type": "10-K",
            "filing_date": "2024-11-01",
            "report_period": "2024-09-28",
            "source_url": "https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/0000320193-24-000123-index.htm",
            "local_path": "demo/filings/AAPL_10-K_2024.html",
            "checksum": "demo_checksum_aapl_10k_2024",
            "parser_status": "completed",
            "embedding_status": "completed",
            "indexing_status": "completed",
        },
        {
            "accession_number": "0000320193-24-000098",
            "filing_type": "10-Q",
            "filing_date": "2024-08-02",
            "report_period": "2024-06-29",
            "source_url": "https://www.sec.gov/Archives/edgar/data/320193/000032019324000098/0000320193-24-000098-index.htm",
            "local_path": "demo/filings/AAPL_10-Q_2024_Q3.html",
            "checksum": "demo_checksum_aapl_10q_2024_q3",
            "parser_status": "completed",
            "embedding_status": "completed",
            "indexing_status": "completed",
        },
    ],
    "MSFT": [
        {
            "accession_number": "0000789019-24-000156",
            "filing_type": "10-K",
            "filing_date": "2024-10-24",
            "report_period": "2024-06-30",
            "source_url": "https://www.sec.gov/Archives/edgar/data/789019/000078901924000156/0000789019-24-000156-index.htm",
            "local_path": "demo/filings/MSFT_10-K_2024.html",
            "checksum": "demo_checksum_msft_10k_2024",
            "parser_status": "completed",
            "embedding_status": "completed",
            "indexing_status": "completed",
        },
        {
            "accession_number": "0000789019-24-000134",
            "filing_type": "10-Q",
            "filing_date": "2024-07-30",
            "report_period": "2024-03-31",
            "source_url": "https://www.sec.gov/Archives/edgar/data/789019/000078901924000134/0000789019-24-000134-index.htm",
            "local_path": "demo/filings/MSFT_10-Q_2024_Q3.html",
            "checksum": "demo_checksum_msft_10q_2024_q3",
            "parser_status": "completed",
            "embedding_status": "completed",
            "indexing_status": "completed",
        },
    ],
    "GOOGL": [
        {
            "accession_number": "0001652044-24-000087",
            "filing_type": "10-K",
            "filing_date": "2024-02-02",
            "report_period": "2023-12-31",
            "source_url": "https://www.sec.gov/Archives/edgar/data/1652044/000165204424000087/0001652044-24-000087-index.htm",
            "local_path": "demo/filings/GOOGL_10-K_2023.html",
            "checksum": "demo_checksum_googl_10k_2023",
            "parser_status": "completed",
            "embedding_status": "completed",
            "indexing_status": "completed",
        },
    ],
    "AMZN": [
        {
            "accession_number": "0001018724-24-000045",
            "filing_type": "10-K",
            "filing_date": "2024-02-01",
            "report_period": "2023-12-31",
            "source_url": "https://www.sec.gov/Archives/edgar/data/1018724/000101872424000045/0001018724-24-000045-index.htm",
            "local_path": "demo/filings/AMZN_10-K_2023.html",
            "checksum": "demo_checksum_amzn_10k_2023",
            "parser_status": "completed",
            "embedding_status": "completed",
            "indexing_status": "completed",
        },
    ],
    "TSLA": [
        {
            "accession_number": "0001318605-24-000034",
            "filing_type": "10-K",
            "filing_date": "2024-01-26",
            "report_period": "2023-12-31",
            "source_url": "https://www.sec.gov/Archives/edgar/data/1318605/000131860524000034/0001318605-24-000034-index.htm",
            "local_path": "demo/filings/TSLA_10-K_2023.html",
            "checksum": "demo_checksum_tsla_10k_2023",
            "parser_status": "completed",
            "embedding_status": "completed",
            "indexing_status": "completed",
        },
    ],
}


class DemoSECService:
    """
    Deterministic demo SEC filing service.

    Returns curated synthetic SEC filings for a fixed set of demo tickers.
    All values are clearly labeled as DEMO / SYNTHETIC DATA.
    """

    def get_company(self, ticker: str) -> dict[str, Any]:
        """
        Retrieve a demo company profile.

        Args:
            ticker: The ticker symbol (must be one of the demo tickers).

        Returns:
            A demo company dictionary.

        Raises:
            ValueError: If the ticker is not available in demo mode.
        """
        ticker = normalize_ticker(ticker)

        if not is_demo_ticker(ticker):
            raise ValueError(
                f"Demo mode only supports: {', '.join(sorted(DEMO_TICKERS))}"
            )

        # Return a minimal company dict compatible with CompanyMapper
        return {
            "ticker": ticker,
            "cik": "0",
            "name": f"{ticker} Inc. [DEMO / SYNTHETIC DATA]",
            "exchange": "NASDAQ",
            "sector": "Technology",
            "industry": "Software",
            "country": "USA",
            "currency": "USD",
            "website": None,
            "market_cap": None,
        }

    def get_latest_filings(
        self,
        ticker: str,
        form: str = "10-K",
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Retrieve demo SEC filings.

        Args:
            ticker: The ticker symbol (must be one of the demo tickers).
            form: The type of filing to retrieve (e.g., "10-K", "10-Q").
            limit: Maximum number of filings to return.

        Returns:
            A list of demo filing records.
        """
        ticker = normalize_ticker(ticker)

        if not is_demo_ticker(ticker):
            return []

        filings = DEMO_FILINGS.get(ticker, [])
        filtered = [f for f in filings if f["filing_type"] == form]
        return filtered[:limit]

    def get_filing_by_accession(
        self,
        ticker: str,
        accession_number: str,
    ) -> dict[str, Any] | None:
        """Retrieve a specific demo filing by accession number."""
        ticker = normalize_ticker(ticker)
        filings = DEMO_FILINGS.get(ticker, [])
        for filing in filings:
            if filing["accession_number"] == accession_number:
                return filing
        return None

    def get_filings_by_date_range(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
        filing_type: FilingType | str | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve demo filings within a date range."""
        ticker = normalize_ticker(ticker)
        filings = DEMO_FILINGS.get(ticker, [])

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