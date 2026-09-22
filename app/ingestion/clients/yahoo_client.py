from __future__ import annotations
import logging
import yfinance as yf
from app.utils.tickers import normalize_ticker
logger = logging.getLogger(__name__)
class YahooClient:
    def get_info(
        self,
        ticker: str,
    ) -> dict:
        logger.info("Fetching Yahoo Finance info for %s", ticker)
        stock = yf.Ticker(normalize_ticker(ticker))
        return stock.info
    def get_history(
        self,
        ticker: str,
        period: str = "1y",
    ):
        logger.info(
            "Fetching %s history for %s",
            period,
            ticker,
        )
        stock = yf.Ticker(normalize_ticker(ticker))
        return stock.history(period=period)