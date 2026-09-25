from __future__ import annotations

import logging
import os
from typing import Any

from edgar import Company

from app.core.config import settings
from app.data.sec_edgar import SECRateLimiter
from app.utils.tickers import normalize_ticker

logger = logging.getLogger(__name__)


class EdgarClient:
    """
    Client for interacting with SEC EDGAR through edgartools.

    All operations that can trigger SEC EDGAR network requests are
    protected by the distributed Redis-backed SEC rate limiter.
    """

    def __init__(self) -> None:
        if not settings.edgar_identity:
            raise ValueError(
                "EDGAR_IDENTITY is missing. Please set it in the .env file."
            )

        os.environ["EDGAR_IDENTITY"] = settings.edgar_identity

        # Shared Redis-backed token bucket.
        #
        # The limiter is intentionally created once per EdgarClient and
        # uses a Redis key shared by all application workers.
        self._sec_rate_limiter = SECRateLimiter()

        logger.info("EdgarClient initialized.")

    def get_company(
        self,
        ticker: str,
    ) -> Company:
        """
        Create an edgartools Company instance for a ticker.

        Company construction itself is kept separate from the rate-limited
        EDGAR operations. The actual filing retrieval is protected in
        get_filings().
        """

        logger.info("Fetching company: %s", ticker)

        return Company(normalize_ticker(ticker))

    def get_filings(
        self,
        ticker: str,
        form: str = "10-K",
        limit: int = 5,
    ) -> Any:
        """
        Fetch SEC filings for a company.

        The SEC rate limiter is acquired immediately before the EDGAR
        filing request.
        """

        logger.info(
            "Fetching %s filings for %s",
            form,
            ticker,
        )

        company = self.get_company(ticker)

        # company.get_filings() can perform an SEC EDGAR network request.
        self._sec_rate_limiter.acquire()

        filings = company.get_filings(
            form=form,
        )

        return filings[:limit]

    def download_filing(
        self,
        filing,
    ) -> str:
        """
        Download the HTML contents of a filing.

        The SEC rate limiter is acquired immediately before the network
        operation.
        """

        logger.info(
            "Downloading filing %s",
            filing.accession_number,
        )

        # filing.html() can perform an SEC EDGAR network request.
        self._sec_rate_limiter.acquire()

        return filing.html()