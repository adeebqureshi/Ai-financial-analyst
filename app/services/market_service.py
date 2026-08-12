"""
Market Service

This module contains the business logic for retrieving live market data.
It delegates to the existing ``MarketService`` from ingestion and wraps the
results in typed response DTOs.
"""

from __future__ import annotations

from app.core.config import Settings
from app.core.logging import get_logger
from app.ingestion.services.market_service import MarketService as IngestionMarketService
from app.models.market import MarketData
from app.schemas.responses import MarketDataResponse

logger = get_logger(__name__)


class MarketService:
    """
    Service for retrieving live market data.

    Attributes:
        _settings: Application settings instance.
        _market: Ingestion market service for data retrieval.
    """

    def __init__(self, settings: Settings) -> None:
        """
        Initialize the market service.

        Args:
            settings: The application settings instance.
        """
        self._settings = settings
        self._market = IngestionMarketService()

    def get_market_data(self, ticker: str) -> MarketDataResponse:
        """
        Retrieve live market data for a company.

        Args:
            ticker: The ticker symbol (e.g., "AAPL").

        Returns:
            A ``MarketDataResponse`` with current market data.
        """
        ticker = ticker.upper()

        try:
            data = self._market.get_market_data(ticker)
            return self._to_response(data)
        except Exception as exc:
            logger.warning(
                "Failed to retrieve market data for %s: %s",
                ticker,
                exc,
            )
            return MarketDataResponse(
                ticker=ticker,
                exchange="UNKNOWN",
                current_price=0.0,
            )

    def get_market_data_batch(self, tickers: list[str]) -> dict[str, MarketDataResponse]:
        """
        Retrieve market data for multiple tickers.

        Args:
            tickers: List of ticker symbols.

        Returns:
            Dictionary mapping ticker to market data response.
        """
        results = {}
        for ticker in tickers:
            results[ticker.upper()] = self.get_market_data(ticker)
        return results

    def _to_response(self, data: MarketData) -> MarketDataResponse:
        """
        Convert internal MarketData model to API response model.

        Args:
            data: Internal market data model.

        Returns:
            MarketDataResponse for API consumption.
        """
        return MarketDataResponse(
            ticker=data.ticker,
            exchange=data.exchange.value if hasattr(data.exchange, "value") else str(data.exchange),
            current_price=data.current_price,
            currency=data.currency,
            market_cap=data.market_cap,
            volume=data.volume,
            beta=data.beta,
            pe_ratio=data.pe_ratio,
            eps=data.eps,
            dividend_yield=data.dividend_yield,
            week_52_high=data.week_52_high,
            week_52_low=data.week_52_low,
        )