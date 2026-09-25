from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

from app.demo.fixtures.companies import (
    DEMO_MARKET_QUOTES,
    get_demo_market_data,
    is_demo_ticker,
)
from app.ingestion.providers.base import (
    MarketDataProvider,
    ProviderError,
    Quote,
    validate_quote,
)

logger = logging.getLogger(__name__)


class DemoMarketProvider(MarketDataProvider):
    name = "demo"

    def fetch_quote(
        self,
        ticker: str,
        timeout_seconds: float = 10.0,
    ) -> Quote:
        # Demo data must never be usable in production.
        if os.getenv("ENV", "").strip().lower() == "production":
            raise ProviderError(
                "Demo market provider is disabled in production."
            )

        ticker = ticker.upper()

        if not is_demo_ticker(ticker):
            raise ProviderError(
                "Demo provider only supports: "
                f"{', '.join(sorted(DEMO_MARKET_QUOTES.keys()))}"
            )

        market_data = get_demo_market_data(ticker)

        quote = Quote(
            ticker=ticker,
            provider=self.name,
            price=market_data.current_price,
            quote_time=market_data.provider_time,
            currency=market_data.currency,
            exchange=(
                market_data.exchange.value
                if market_data.exchange
                else "NASDAQ"
            ),
            volume=market_data.volume,
            market_cap=market_data.market_cap,
            beta=market_data.beta,
            pe_ratio=market_data.pe_ratio,
            eps=market_data.eps,
            dividend_yield=market_data.dividend_yield,
            week_52_high=market_data.week_52_high,
            week_52_low=market_data.week_52_low,
            fetched_at=datetime.now(timezone.utc),
        )

        return validate_quote(quote)