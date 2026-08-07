"""
Yahoo Finance provider.
"""

from __future__ import annotations

import yfinance as yf

from app.data.company import Company
from app.data.market_data import MarketData


class YahooFinanceProvider:

    def company(
        self,
        ticker: str,
    ) -> Company:

        info = yf.Ticker(ticker).info

        return Company(
            ticker=ticker.upper(),
            name=info.get("longName", ticker),
            sector=info.get("sector", ""),
            industry=info.get("industry", ""),
            exchange=info.get("exchange", ""),
        )

    def market_data(
        self,
        ticker: str,
    ) -> MarketData:

        info = yf.Ticker(ticker).info

        return MarketData(
            price=float(info.get("currentPrice", 0)),
            market_cap=float(info.get("marketCap", 0)),
            pe_ratio=float(info.get("trailingPE", 0)),
            eps=float(info.get("trailingEps", 0)),
            volume=int(info.get("volume", 0)),
        )