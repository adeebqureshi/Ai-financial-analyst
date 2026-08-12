"""
Tests for the layout-aware Markdown table parser.
"""

from __future__ import annotations

import pytest

from app.parsers.table_parser import ParsedTable, TableParser


@pytest.fixture()
def parser() -> TableParser:
    return TableParser()


def test_basic_table(parser: TableParser) -> None:
    markdown = (
        "| Revenue | COGS | Gross Profit |\n"
        "|---|---|---|\n"
        "| 500 | 200 | 300 |\n"
    )

    tables = parser.parse(markdown)

    assert len(tables) == 1

    table = tables[0]

    assert isinstance(table, ParsedTable)

    assert table.headers == ["Revenue", "COGS", "Gross Profit"]

    assert table.row_count == 1

    assert table.rows == [["500", "200", "300"]]


def test_multiple_rows_and_columns(parser: TableParser) -> None:
    markdown = (
        "| 2024 | 2023 | 2022 |\n"
        "|---|---|---|\n"
        "| 1,250,000 | 1,100,000 | 950,000 |\n"
        "| 400,000 | 380,000 | 350,000 |\n"
    )

    tables = parser.parse(markdown)

    assert len(tables) == 1

    table = tables[0]

    assert table.column_count == 3

    assert table.row_count == 2

    assert table.rows[0] == ["1,250,000", "1,100,000", "950,000"]

    assert table.rows[1] == ["400,000", "380,000", "350,000"]


def test_empty_cells(parser: TableParser) -> None:
    markdown = (
        "| Metric | 2024 | 2023 |\n"
        "|---|---|---|\n"
        "| Revenue | 500 | |\n"
        "| COGS | | 200 |\n"
    )

    table = parser.parse(markdown)[0]

    assert table.rows[0] == ["Revenue", "500", ""]

    assert table.rows[1] == ["COGS", "", "200"]


def test_parenthesised_negatives_preserved(parser: TableParser) -> None:
    markdown = (
        "| Item | Amount |\n"
        "|---|---|\n"
        "| Net Income | (500) |\n"
        "| Operating Loss | (1,250) |\n"
    )

    table = parser.parse(markdown)[0]

    assert table.rows[0][1] == "(500)"

    assert table.rows[1][1] == "(1,250)"


def test_currency_and_percentages(parser: TableParser) -> None:
    markdown = (
        "| Item | Value |\n"
        "|---|---|\n"
        "| Revenue | $1,250,000 |\n"
        "| Margin | 12.5% |\n"
        "| Euro | \u20ac500 |\n"
    )

    table = parser.parse(markdown)[0]

    assert table.rows[0][1] == "$1,250,000"

    assert table.rows[1][1] == "12.5%"

    assert table.rows[2][1] == "\u20ac500"


def test_footnote_markers_stripped(parser: TableParser) -> None:
    markdown = (
        "| Revenue | 500 |\n"
        "|---|---|\n"
        "| Revenue [1] | 500* |\n"
    )

    table = parser.parse(markdown)[0]

    assert table.rows[0][0] == "Revenue"

    assert table.rows[0][1] == "500"


def test_varying_column_counts_are_padded(parser: TableParser) -> None:
    markdown = (
        "| Metric | 2024 | 2023 |\n"
        "|---|---|---|\n"
        "| Revenue | 500 |\n"
        "| COGS | 200 | 150 |\n"
    )

    table = parser.parse(markdown)[0]

    assert table.rows[0] == ["Revenue", "500", ""]

    assert table.rows[1] == ["COGS", "200", "150"]


def test_table_without_separator_row(parser: TableParser) -> None:
    markdown = (
        "| Year | EPS |\n"
        "| 2024 | 6.16 |\n"
        "| 2023 | 6.13 |\n"
    )

    tables = parser.parse(markdown)

    assert len(tables) == 1

    table = tables[0]

    assert table.headers == ["Year", "EPS"]

    assert table.row_count == 2


def test_title_from_preceding_heading(parser: TableParser) -> None:
    markdown = (
        "# Income Statement\n\n"
        "| Revenue | COGS | Gross Profit |\n"
        "|---|---|---|\n"
        "| 500 | 200 | 300 |\n"
    )

    table = parser.parse(markdown)[0]

    assert table.title == "Income Statement"


def test_title_from_short_caption(parser: TableParser) -> None:
    markdown = (
        "Cash Flow Summary\n\n"
        "| Operating | Investing |\n"
        "|---|---|\n"
        "| 100 | 50 |\n"
    )

    table = parser.parse(markdown)[0]

    assert table.title == "Cash Flow Summary"


def test_source_page_is_preserved(parser: TableParser) -> None:
    markdown = (
        "| Revenue | 500 |\n"
        "|---|---|\n"
        "| COGS | 200 |\n"
    )

    table = parser.parse(markdown, source_page=7)[0]

    assert table.source_page == 7


def test_prose_without_pipes_produces_no_tables(parser: TableParser) -> None:
    markdown = (
        "Revenue increased by 25% year over year.\n"
        "Costs remained stable at 200 million.\n"
    )

    tables = parser.parse(markdown)

    assert tables == []


def test_multiple_tables_are_isolated(parser: TableParser) -> None:
    markdown = (
        "| A | B |\n|---|---|\n| 1 | 2 |\n\n"
        "Some narrative between the tables.\n\n"
        "| C | D |\n|---|---|\n| 3 | 4 |\n"
    )

    tables = parser.parse(markdown)

    assert len(tables) == 2

    assert tables[0].rows == [["1", "2"]]

    assert tables[1].rows == [["3", "4"]]


def test_to_dict_roundtrip(parser: TableParser) -> None:
    markdown = (
        "| Revenue | 500 |\n"
        "|---|---|\n"
        "| COGS | 200 |\n"
    )

    table = parser.parse(markdown, source_page=3)[0]

    data = table.to_dict()

    assert data["headers"] == ["Revenue", "500"]

    assert data["rows"] == [["COGS", "200"]]

    assert data["source_page"] == 3