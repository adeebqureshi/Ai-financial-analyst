"""
Historical prices.
"""

from __future__ import annotations

import yfinance as yf


class HistoricalData:

    def history(
        self,
        ticker: str,
        period: str = "1y",
    ):

        return yf.Ticker(
            ticker,
        ).history(
            period=period,
        )