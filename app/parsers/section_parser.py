"""
section_parser.py

Extracts logical sections from SEC filings.
"""

from __future__ import annotations

import re


class SectionParser:
    """
    Splits SEC filings into logical sections.
    """

    SECTION_PATTERNS = [
        r"ITEM\s+1\.\s+BUSINESS",
        r"ITEM\s+1A\.\s+RISK\s+FACTORS",
        r"ITEM\s+1B\.\s+UNRESOLVED\s+STAFF\s+COMMENTS",
        r"ITEM\s+2\.\s+PROPERTIES",
        r"ITEM\s+3\.\s+LEGAL\s+PROCEEDINGS",
        r"ITEM\s+5\.",
        r"ITEM\s+7\.\s+MANAGEMENT'?S?\s+DISCUSSION",
        r"ITEM\s+7A\.",
        r"ITEM\s+8\.\s+FINANCIAL\s+STATEMENTS",
        r"ITEM\s+9\.",
    ]

    def split(self, text: str) -> dict[str, str]:
        """
        Split filing into sections.

        Returns
        -------
        dict[str, str]
            Mapping of section title -> section text.
        """

        matches = []

        upper = text.upper()

        for pattern in self.SECTION_PATTERNS:
            for match in re.finditer(pattern, upper):
                matches.append((match.start(), match.group()))

        matches.sort()

        if not matches:
            return {"FULL_DOCUMENT": text}

        sections = {}

        for i, (start, title) in enumerate(matches):

            end = len(text)

            if i + 1 < len(matches):
                end = matches[i + 1][0]

            sections[title] = text[start:end].strip()

        return sections