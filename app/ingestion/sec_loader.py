"""
SEC EDGAR document loader.
"""

from __future__ import annotations

from pathlib import Path

import requests

from app.ingestion.document import FinancialDocument
from app.ingestion.loader import DocumentLoader
from app.ingestion.metadata import DocumentMetadata


class SECLoader(DocumentLoader):
    """
    Downloads SEC filings from EDGAR.
    """

    USER_AGENT = (
        "AI Financial Analyst "
        "(research@example.com)"
    )

    def load(
        self,
        url: str,
    ) -> FinancialDocument:

        response = requests.get(
            url,
            headers={
                "User-Agent": self.USER_AGENT,
            },
            timeout=30,
        )

        response.raise_for_status()

        return FinancialDocument(
            text=response.text,
            metadata=DocumentMetadata(
                source="sec",
                filename=Path(url).name,
                mime_type="text/html",
            ),
        )