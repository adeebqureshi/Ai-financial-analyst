"""
HTML document loader.
"""

from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup

from app.ingestion.document import FinancialDocument
from app.ingestion.loader import DocumentLoader
from app.ingestion.metadata import DocumentMetadata


class HTMLLoader(DocumentLoader):
    """
    Loads HTML financial documents.
    """

    def load(
        self,
        path: str,
    ) -> FinancialDocument:

        html = Path(path).read_text(
            encoding="utf-8",
        )

        soup = BeautifulSoup(
            html,
            "lxml",
        )

        text = soup.get_text(
            separator="\n",
            strip=True,
        )

        return FinancialDocument(
            text=text,
            metadata=DocumentMetadata(
                source="html",
                filename=Path(path).name,
                mime_type="text/html",
            ),
        )