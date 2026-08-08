"""
market_service.py

Business service for retrieving market data.
"""

from __future__ import annotations

from app.enums.exchange import Exchange
from app.ingestion.clients.yahoo_client import YahooClient
from app.models.market import MarketData


class MarketService:
    """
    Service responsible for retrieving live market data.
    """

    def __init__(self) -> None:
        self.client = YahooClient()

    def get_market_data(
        self,
        ticker: str,
    ) -> MarketData:
        """
        Retrieve market data from Yahoo Finance.
        """

        info = self.client.get_info(ticker)

        exchange = Exchange.NASDAQ

        exchange_name = str(info.get("exchange", "")).upper()

        if "NYSE" in exchange_name:
            exchange = Exchange.NYSE
        elif "NASDAQ" in exchange_name:
            exchange = Exchange.NASDAQ

        current_price = info.get("currentPrice") or info.get("regularMarketPrice") or 0.0

        return MarketData(
            ticker=ticker.upper(),
            exchange=exchange,
            current_price=current_price,
            currency=info.get("currency", "USD"),
            market_cap=info.get("marketCap"),
            volume=info.get("volume"),
            beta=info.get("beta"),
            pe_ratio=info.get("trailingPE"),
            eps=info.get("trailingEps"),
            dividend_yield=info.get("dividendYield"),
            week_52_high=info.get("fiftyTwoWeekHigh"),
            week_52_low=info.get("fiftyTwoWeekLow"),
        )