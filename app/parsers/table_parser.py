"""
table_parser.py

Layout-aware Markdown table extraction for financial documents.

LlamaParse and Marker emit tables as GitHub-flavoured Markdown tables.
This parser converts those Markdown blocks into a structured
``ParsedTable`` so columnar financial data (for example
``Revenue | COGS | Gross Profit``) keeps its structure instead of being
reduced to flat text.

Design goals:
    - Reliable extraction of ordinary Markdown tables.
    - Robustness to real-world financial-table quirks: empty cells,
      varying column counts, parenthesised negatives such as ``(500)``,
      thousands separators such as ``1,250,000``, currency symbols,
      percentages and trailing footnote markers.
    - No fabrication. Only Markdown tables that actually exist in the
      source text are returned.

The parser keeps cell values as the literal strings produced by the
upstream parsers (``"1,250,000"``, ``"(500)"``, ``"12.5%"``) rather than
attempting lossy numeric coercion, which would collapse the variety of
formats used across financial statements.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_FOOTNOTE_PATTERN = re.compile(r"\s*(?:\[\d+\]|\([a-z]\)|[*†‡§])\s*$")

_ALIGNMENT_PATTERN = re.compile(r"^:?-+:?$")

_HEADING_PATTERN = re.compile(r"^#+\s*(.*)$")

_TITLE_LIMIT = 60

_MAX_TITLE_LOOKBACK = 4

_MIN_PIPES = 2


@dataclass(slots=True)
class ParsedTable:
    """
    A structured financial table extracted from Markdown output.
    """

    title: str
    headers: list[str] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)
    source_page: int | None = None

    @property
    def row_count(self) -> int:
        """Number of data rows (excluding the header row)."""
        return len(self.rows)

    @property
    def column_count(self) -> int:
        """Number of header columns."""
        return len(self.headers)

    def to_dict(self) -> dict[str, object]:
        """
        Serialize the table for storage in vector-store payloads.
        """
        return {
            "title": self.title,
            "headers": list(self.headers),
            "rows": [list(row) for row in self.rows],
            "source_page": self.source_page,
        }


class TableParser:
    """
    Parses Markdown tables into structured :class:`ParsedTable` objects.
    """

    def parse(
        self,
        text: str,
        source_page: int | None = None,
    ) -> list[ParsedTable]:
        """
        Parse Markdown tables from ``text``.

        Args:
            text: Markdown output produced by LlamaParse/Marker.
            source_page: Optional 1-based page number the text belongs to.

        Returns:
            A list of structured tables found in the text.
        """
        return self.parse_markdown(text, source_page=source_page)

    def parse_markdown(
        self,
        text: str,
        source_page: int | None = None,
    ) -> list[ParsedTable]:
        """
        Parse Markdown tables from ``text``.

        See :meth:`parse`.
        """
        lines = text.splitlines()

        tables: list[ParsedTable] = []

        start = 0

        while start < len(lines):

            if not self._is_table_line(lines[start]):
                start += 1
                continue

            end = start

            while end < len(lines) and self._is_table_line(lines[end]):
                end += 1

            title = self._detect_title(lines, start)

            table = self._build(
                lines[start:end],
                title=title,
                source_page=source_page,
            )

            if table is not None:
                tables.append(table)

            start = end

        return tables

    # ── Line / row recognition ──────────────────────────────────────────

    @staticmethod
    def _is_table_line(line: str) -> bool:
        """Whether ``line`` looks like a Markdown table row."""
        stripped = line.strip()

        if not stripped:
            return False

        if stripped.count("|") < _MIN_PIPES:
            return False

        # A block of pipes with no text (e.g. a long divider) is not a row.
        return bool(stripped.strip("| "))

    @staticmethod
    def _split_row(line: str) -> list[str]:
        """Split a Markdown table row into raw (uncleaned) cells."""
        stripped = line.strip()

        if stripped.startswith("|"):
            stripped = stripped[1:]

        if stripped.endswith("|"):
            stripped = stripped[:-1]

        return [cell.strip() for cell in stripped.split("|")]

    @staticmethod
    def _is_separator(row: list[str]) -> bool:
        """Whether ``row`` is a Markdown alignment separator (``|---|---|``)."""
        non_empty = [cell for cell in row if cell.strip()]

        if not non_empty:
            return False

        return all(
            _ALIGNMENT_PATTERN.match(cell.strip()) is not None
            for cell in non_empty
        )

    # ── Table construction ──────────────────────────────────────────────

    def _build(
        self,
        lines: list[str],
        title: str,
        source_page: int | None,
    ) -> ParsedTable | None:
        """Build a :class:`ParsedTable` from a contiguous table block."""
        rows = [self._split_row(line) for line in lines]

        # A separator immediately after the header, when present, is dropped.
        if len(rows) >= 2 and self._is_separator(rows[1]):
            headers = rows[0]
            data = rows[2:]
        else:
            headers = rows[0]
            data = rows[1:]

        if not data:
            return None

        headers = self._clean_row(headers)

        width = len(headers)

        cleaned_rows: list[list[str]] = []

        for row in data:
            cleaned = self._clean_row(row)

            if len(cleaned) < width:
                cleaned = cleaned + [""] * (width - len(cleaned))

            cleaned_rows.append(cleaned)

        return ParsedTable(
            title=title,
            headers=headers,
            rows=cleaned_rows,
            source_page=source_page,
        )

    # ── Title detection ─────────────────────────────────────────────────

    @staticmethod
    def _detect_title(lines: list[str], start: int) -> str:
        """
        Best-effort title from the lines preceding a table block.

        Prefers a Markdown heading; otherwise accepts a short caption line.
        Sentence-like prose (ending with sentence punctuation) is rejected so
        narrative text is not misattributed as a table title. Blank lines are
        skipped, and the lookback is bounded so a distant unrelated heading is
        not captured.
        """
        index = start - 1

        candidates_seen = 0

        while index >= 0 and candidates_seen <= _MAX_TITLE_LOOKBACK:
            line = lines[index].strip()

            index -= 1

            if not line:
                continue

            candidates_seen += 1

            if TableParser._is_table_line(line):
                return ""

            heading = _HEADING_PATTERN.match(line)

            if heading is not None:
                return heading.group(1).strip()

            if (
                len(line) <= _TITLE_LIMIT
                and not line.endswith((".", "?", "!", ":"))
            ):
                return line

            return ""

        return ""

    # ── Cell cleaning ───────────────────────────────────────────────────

    @classmethod
    def _clean_row(cls, row: list[str]) -> list[str]:
        """Trim whitespace and strip trailing footnote markers per cell."""
        return [cls._clean_cell(cell) for cell in row]

    @staticmethod
    def _clean_cell(cell: str) -> str:
        """
        Trim a cell and strip trailing footnote markers.

        Parenthesised negatives such as ``(500)`` are preserved because the
        footnote pattern only targets bracketed references/symbols, not
        numeric values.
        """
        value = cell.strip()

        if not value:
            return ""

        cleaned = _FOOTNOTE_PATTERN.sub("", value).strip()

        return cleaned or value