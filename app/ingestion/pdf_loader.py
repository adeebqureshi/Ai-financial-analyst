"""
PDF document loader.
"""

from __future__ import annotations

from pathlib import Path

import fitz

from app.ingestion.document import FinancialDocument
from app.ingestion.loader import DocumentLoader
from app.ingestion.metadata import DocumentMetadata


class PDFLoader(DocumentLoader):
    """
    Loads PDF financial documents using PyMuPDF.
    """

    def load(
        self,
        path: str,
    ) -> FinancialDocument:

        pdf = fitz.open(path)

        pages: list[str] = []

        for page in pdf:
            pages.append(page.get_text())

        pdf.close()

        return FinancialDocument(
            text="\n".join(pages),
            metadata=DocumentMetadata(
                source="pdf",
                filename=Path(path).name,
                mime_type="application/pdf",
            ),
        )