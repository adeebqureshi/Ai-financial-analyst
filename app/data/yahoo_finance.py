from __future__ import annotations
import math
import yfinance as yf
from app.data.company import Company
from app.data.market_data import MarketData
from app.utils.tickers import normalize_ticker
def _finite(value):
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None
class YahooFinanceProvider:
    def company(
        self,
        ticker: str,
    ) -> Company:
        ticker = normalize_ticker(ticker)
        info = yf.Ticker(ticker).info
        return Company(
            ticker=ticker,
            name=info.get("longName", ticker),
            sector=info.get("sector", ""),
            industry=info.get("industry", ""),
            exchange=info.get("exchange", ""),
        )
    def market_data(
        self,
        ticker: str,
    ) -> MarketData:
        ticker = normalize_ticker(ticker)
        info = yf.Ticker(ticker).info
        return MarketData(
            price=_finite(info.get("currentPrice")),
            market_cap=_finite(info.get("marketCap")),
            pe_ratio=_finite(info.get("trailingPE")),
            eps=_finite(info.get("trailingEps")),
            volume=_finite(info.get("volume")),
        )