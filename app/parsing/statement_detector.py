"""
Financial statement detector.
"""

from __future__ import annotations

from app.parsing.section import Section
from app.parsing.statement import FinancialStatement


class StatementDetector:
    """
    Detects common financial statements from parsed sections.
    """

    KEYWORDS = (
        "balance sheet",
        "income statement",
        "statement of operations",
        "cash flow",
        "cash flows",
        "shareholders' equity",
        "stockholders' equity",
    )

    def detect(
        self,
        sections: list[Section],
    ) -> list[FinancialStatement]:

        statements: list[FinancialStatement] = []

        for section in sections:

            title = section.title.lower()

            for keyword in self.KEYWORDS:

                if keyword in title:
                    statements.append(
                        FinancialStatement(
                            name=section.title,
                            content=section.content,
                        )
                    )
                    break

        return statements