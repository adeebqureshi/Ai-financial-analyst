"""
Simple filing parser.
"""

from __future__ import annotations

from app.data.filing_section import FilingSection


class FilingParser:

    def parse(
        self,
        text: str,
    ) -> list[FilingSection]:

        blocks = [
            block.strip()
            for block in text.split("\n\n")
            if block.strip()
        ]

        sections: list[FilingSection] = []

        for index, block in enumerate(blocks, start=1):

            sections.append(
                FilingSection(
                    title=f"Section {index}",
                    content=block,
                )
            )

        return sections