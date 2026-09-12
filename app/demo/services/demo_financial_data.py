"""
Demo Financial Data Service

Deterministic financial data service for demo mode.
Provides synthetic financial statements, risk scores, and company profiles.
"""

from __future__ import annotations

from app.core.config import get_settings
from app.core.exceptions import RetrievalError
from app.demo.fixtures.companies import (
    DEMO_TICKERS,
    get_demo_company,
    get_demo_financial_statement,
    get_demo_market_data,
    get_demo_risk_scores,
    get_demo_growth_rate,
    get_demo_tax_rate,
    get_demo_description,
    is_demo_ticker,
)
from app.financial.data import CompanyFinancialData
from app.financial.models import FinancialStatement
from app.models.company import Company
from app.models.market import MarketData
from app.utils.tickers import normalize_ticker


class DemoFinancialDataService:
    """
    Deterministic demo financial data service.

    Returns curated synthetic financial data for a fixed set of demo tickers.
    All values are clearly labeled as DEMO / SYNTHETIC DATA.
    """

    def __init__(self) -> None:
        self._cache: dict[str, CompanyFinancialData] = {}

    def load(self, ticker: str) -> CompanyFinancialData:
        """
        Return normalized company-specific financial data for ``ticker``.

        Args:
            ticker: Ticker symbol (must be one of the demo tickers).

        Returns:
            A ``CompanyFinancialData`` built from synthetic demo data.

        Raises:
            RetrievalError: If the ticker is not available in demo mode.
        """
        ticker = normalize_ticker(ticker)

        if ticker in self._cache:
            return self._cache[ticker]

        if not is_demo_ticker(ticker):
            raise RetrievalError(
                message=(
                    f"Demo mode only supports: {', '.join(sorted(DEMO_TICKERS))}"
                ),
                error_code="DEMO_001",
                details={"ticker": ticker, "available": DEMO_TICKERS},
            )

        data = self._build_demo_data(ticker)
        self._cache[ticker] = data
        return data

    def get_statement(self, ticker: str) -> FinancialStatement:
        """Return the normalized financial statement for ``ticker``."""
        return self.load(ticker).statement

    def clear_cache(self, ticker: str | None = None) -> None:
        """Clear the cached financial data."""
        if ticker is None:
            self._cache.clear()
        else:
            self._cache.pop(normalize_ticker(ticker), None)

    def _build_demo_data(self, ticker: str) -> CompanyFinancialData:
        """Build demo CompanyFinancialData from fixtures."""
        company = get_demo_company(ticker)
        statement = get_demo_financial_statement(ticker)
        market = get_demo_market_data(ticker)
        risk_scores = get_demo_risk_scores(ticker)

        return CompanyFinancialData(
            ticker=ticker,
            statement=statement,
            piotroski_score=risk_scores["piotroski_score"],  # type: ignore
            altman_score=risk_scores["altman_score"],  # type: ignore
            beneish_score=risk_scores["beneish_score"],  # type: ignore
            growth_rate=get_demo_growth_rate(ticker),
            beta=market.beta,
            tax_rate=get_demo_tax_rate(ticker),
            current_price=market.current_price,
            price_available=market.current_price is not None,
            name=company.name,
            sector=company.sector,
            industry=company.industry,
            market_cap=market.market_cap,
            description=get_demo_description(ticker),
        )