from __future__ import annotations

import logging
import os
from typing import Any

from edgar import Company

from app.core.config import settings
from app.data.sec_http import (
    SECRequestGateway,
    get_sec_gateway,
    install_edgar_sec_enforcement,
)
from app.utils.tickers import normalize_ticker

logger = logging.getLogger(__name__)


class EdgarClient:
    """Client for interacting with SEC EDGAR through edgartools.

    edgartools performs its own HTTP I/O with its own transport and internal
    retries. Instead of relying on a "acquire before the call" convention, this
    client binds edgartools' HTTP transport - and its two raw httpx helpers -
    to the centralized SEC gateway limiter. Every EDGAR request, including
    edgartools' internal retries, is therefore admitted by the same
    distributed Redis-enforced rate limiter as every other SEC client.
    """

    def __init__(self) -> None:
        if not settings.edgar_identity:
            raise ValueError(
                "EDGAR_IDENTITY is missing. Please set it in the .env file."
            )

        os.environ["EDGAR_IDENTITY"] = settings.edgar_identity

        # Fail closed: building the gateway requires a reachable Redis.
        self._sec_gateway: SECRequestGateway = get_sec_gateway()

        # The one shared distributed limiter (same Redis key as every other
        # SEC client in this repository). Exposed for backwards compatibility.
        self._sec_rate_limiter = self._sec_gateway.limiter

        if not install_edgar_sec_enforcement(self._sec_gateway):
            raise RuntimeError(
                "Could not bind edgartools to the centralized SEC gateway; "
                "refusing to make unthrottled SEC requests."
            )

        logger.info("EdgarClient initialized with centralized SEC enforcement.")

    def get_company(
        self,
        ticker: str,
    ) -> Company:
        """Create an edgartools Company instance for a ticker.

        Constructing an edgartools ``Company`` can trigger an EDGAR network
        request, which is why the edgartools transport is bound to the
        centralized gateway before any EDGAR call happens.
        """

        logger.info("Fetching company: %s", ticker)

        return Company(normalize_ticker(ticker))

    def get_filings(
        self,
        ticker: str,
        form: str = "10-K",
        limit: int = 5,
    ) -> Any:
        """Fetch SEC filings for a company.

        ``company.get_filings()`` performs an EDGAR request; it goes through
        the centralized gateway limiter bound in ``__init__``.
        """

        logger.info(
            "Fetching %s filings for %s",
            form,
            ticker,
        )

        company = self.get_company(ticker)

        filings = company.get_filings(
            form=form,
        )

        return filings[:limit]

    def download_filing(
        self,
        filing,
    ) -> str:
        """Download the HTML contents of a filing.

        ``filing.html()`` performs EDGAR requests; they go through the
        centralized gateway limiter bound in ``__init__``.
        """

        logger.info(
            "Downloading filing %s",
            filing.accession_number,
        )

        return filing.html()
