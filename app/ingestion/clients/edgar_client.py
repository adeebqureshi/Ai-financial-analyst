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

    def __init__(self) -> None:
        if not settings.edgar_identity:
            raise ValueError(
                "EDGAR_IDENTITY is missing. Please set it in the .env file."
            )

        os.environ["EDGAR_IDENTITY"] = settings.edgar_identity

        self._sec_gateway: SECRequestGateway = get_sec_gateway()

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

        logger.info("Fetching company: %s", ticker)

        return Company(normalize_ticker(ticker))

    def get_filings(
        self,
        ticker: str,
        form: str = "10-K",
        limit: int = 5,
    ) -> Any:

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

        logger.info(
            "Downloading filing %s",
            filing.accession_number,
        )

        return filing.html()
