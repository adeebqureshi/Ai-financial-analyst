from __future__ import annotations
from app.core.config import Settings
from app.core.logging import get_logger
from app.ingestion.services.market_service import MarketService as IngestionMarketService
from app.models.market import MarketData
from app.schemas.responses import MarketDataResponse
from app.utils.tickers import normalize_ticker
logger = get_logger(__name__)
class MarketService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._market = IngestionMarketService(settings)
    def get_market_data(self, ticker: str) -> MarketDataResponse:
        ticker = normalize_ticker(ticker)
        try:
            data = self._market.get_market_data(ticker)
        except Exception as exc:
            logger.warning(
                "Market data unavailable for %s: %s",
                ticker,
                exc,
            )
            return MarketDataResponse(
                ticker=ticker,
                exchange=None,
                current_price=None,
                price_available=False,
            )
        return self._to_response(data)
    def get_market_data_batch(self, tickers: list[str]) -> dict[str, MarketDataResponse]:
        results = {}
        for ticker in tickers:
            results[normalize_ticker(ticker)] = self.get_market_data(ticker)
        return results
    def _to_response(self, data: MarketData) -> MarketDataResponse:
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
            price_available=data.current_price is not None,
            provider=data.provider,
            as_of=data.provider_time,
            cached=data.cached,
            stale=data.stale,
        )