"""
Simple XBRL loader.
"""

from __future__ import annotations

from pathlib import Path

from lxml import etree

from app.ingestion.document import FinancialDocument
from app.ingestion.loader import DocumentLoader
from app.ingestion.metadata import DocumentMetadata


class XBRLLoader(DocumentLoader):
    """
    Loads XBRL financial filings.
    """

    def load(
        self,
        path: str,
    ) -> FinancialDocument:

        tree = etree.parse(path)

        root = tree.getroot()

        text = " ".join(root.itertext())

        return FinancialDocument(
            text=text,
            metadata=DocumentMetadata(
                source="xbrl",
                filename=Path(path).name,
                mime_type="application/xml",
            ),
        )