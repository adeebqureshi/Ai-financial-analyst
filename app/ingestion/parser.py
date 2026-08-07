"""
Basic document parser.
"""

from __future__ import annotations

from pathlib import Path

from app.ingestion.document import FinancialDocument
from app.ingestion.metadata import DocumentMetadata


class PlainTextParser:

    def parse(
        self,
        path: str,
    ) -> FinancialDocument:

        text = Path(path).read_text(
            encoding="utf-8",
        )

        return FinancialDocument(
            text=text,
            metadata=DocumentMetadata(
                source="text",
                filename=Path(path).name,
            ),
        )