"""
yahoo_client.py

Client for retrieving market data from Yahoo Finance.
"""

from __future__ import annotations

import logging

import yfinance as yf


logger = logging.getLogger(__name__)


class YahooClient:
    """
    Wrapper around yfinance.
    """

    def get_info(
        self,
        ticker: str,
    ) -> dict:
        """
        Retrieve company information.
        """

        logger.info("Fetching Yahoo Finance info for %s", ticker)

        stock = yf.Ticker(ticker.upper())

        return stock.info

    def get_history(
        self,
        ticker: str,
        period: str = "1y",
    ):
        """
        Retrieve historical OHLCV data.
        """

        logger.info(
            "Fetching %s history for %s",
            period,
            ticker,
        )

        stock = yf.Ticker(ticker.upper())

        return stock.history(period=period)