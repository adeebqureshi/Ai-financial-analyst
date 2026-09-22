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
    title: str
    headers: list[str] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)
    source_page: int | None = None
    @property
    def row_count(self) -> int:
        return len(self.rows)
    @property
    def column_count(self) -> int:
        return len(self.headers)
    def to_dict(self) -> dict[str, object]:
        return {
            "title": self.title,
            "headers": list(self.headers),
            "rows": [list(row) for row in self.rows],
            "source_page": self.source_page,
        }
class TableParser:
    def parse(
        self,
        text: str,
        source_page: int | None = None,
    ) -> list[ParsedTable]:
        return self.parse_markdown(text, source_page=source_page)
    def parse_markdown(
        self,
        text: str,
        source_page: int | None = None,
    ) -> list[ParsedTable]:
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
    @staticmethod
    def _is_table_line(line: str) -> bool:
        stripped = line.strip()
        if not stripped:
            return False
        if stripped.count("|") < _MIN_PIPES:
            return False
        return bool(stripped.strip("| "))
    @staticmethod
    def _split_row(line: str) -> list[str]:
        stripped = line.strip()
        if stripped.startswith("|"):
            stripped = stripped[1:]
        if stripped.endswith("|"):
            stripped = stripped[:-1]
        return [cell.strip() for cell in stripped.split("|")]
    @staticmethod
    def _is_separator(row: list[str]) -> bool:
        non_empty = [cell for cell in row if cell.strip()]
        if not non_empty:
            return False
        return all(
            _ALIGNMENT_PATTERN.match(cell.strip()) is not None
            for cell in non_empty
        )
    def _build(
        self,
        lines: list[str],
        title: str,
        source_page: int | None,
    ) -> ParsedTable | None:
        rows = [self._split_row(line) for line in lines]
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
    @staticmethod
    def _detect_title(lines: list[str], start: int) -> str:
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
    @classmethod
    def _clean_row(cls, row: list[str]) -> list[str]:
        return [cls._clean_cell(cell) for cell in row]
    @staticmethod
    def _clean_cell(cell: str) -> str:
        value = cell.strip()
        if not value:
            return ""
        cleaned = _FOOTNOTE_PATTERN.sub("", value).strip()
        return cleaned or value