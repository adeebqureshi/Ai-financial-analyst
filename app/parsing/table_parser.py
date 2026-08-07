"""
Simple Markdown table parser.
"""

from __future__ import annotations

from app.parsing.table import FinancialTable


class TableParser:
    """
    Parses Markdown-style tables.
    """

    def parse(
        self,
        text: str,
    ) -> list[FinancialTable]:

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        tables: list[FinancialTable] = []

        current: list[str] = []

        for line in lines:

            if "|" in line:
                current.append(line)
            else:
                if current:
                    tables.append(self._build(current))
                    current = []

        if current:
            tables.append(self._build(current))

        return tables

    def _build(
        self,
        lines: list[str],
    ) -> FinancialTable:

        cleaned = [
            [cell.strip() for cell in line.strip("|").split("|")]
            for line in lines
        ]

        headers = cleaned[0]

        rows = []

        for row in cleaned[2:]:
            rows.append(row)

        return FinancialTable(
            title="Table",
            headers=headers,
            rows=rows,
        )