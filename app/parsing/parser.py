"""
Simple document parser.
"""

from __future__ import annotations

import re

from app.ingestion.document import FinancialDocument
from app.parsing.section import Section


class DocumentParser:
    """
    Splits a document into sections based on Markdown-style headings.
    """

    HEADER_PATTERN = re.compile(r"^#+\s+(.+)$", re.MULTILINE)

    def parse(
        self,
        document: FinancialDocument,
    ) -> list[Section]:

        matches = list(self.HEADER_PATTERN.finditer(document.text))

        if not matches:
            return [
                Section(
                    title="Document",
                    content=document.text.strip(),
                )
            ]

        sections: list[Section] = []

        for index, match in enumerate(matches):
            start = match.end()

            end = (
                matches[index + 1].start()
                if index + 1 < len(matches)
                else len(document.text)
            )

            sections.append(
                Section(
                    title=match.group(1).strip(),
                    content=document.text[start:end].strip(),
                )
            )

        return sections