"""
edgar_client.py

Client for interacting with the SEC EDGAR system.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from edgar import Company

from app.core.config import settings


logger = logging.getLogger(__name__)


class EdgarClient:
    """
    Wrapper around the edgartools library.
    """

    def __init__(self) -> None:
        """
        Configure EDGAR identity.
        """

        if not settings.edgar_identity:
            raise ValueError(
                "EDGAR_IDENTITY is missing. Please set it in the .env file."
            )

        os.environ["EDGAR_IDENTITY"] = settings.edgar_identity

        logger.info("EdgarClient initialized.")

    def get_company(
        self,
        ticker: str,
    ) -> Company:
        """
        Retrieve a company by ticker.
        """

        logger.info("Fetching company: %s", ticker)

        return Company(ticker.upper())

    def get_filings(
        self,
        ticker: str,
        form: str = "10-K",
        limit: int = 5,
    ) -> Any:
        """
        Retrieve SEC filings.
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
        """
        Download filing HTML.

        Parameters
        ----------
        filing
            Filing object returned by edgartools.

        Returns
        -------
        str
            Filing HTML.
        """

        logger.info(
            "Downloading filing %s",
            filing.accession_number,
        )

        return filing.html()