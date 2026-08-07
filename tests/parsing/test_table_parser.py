from app.parsing.table_parser import TableParser


def test_table_parser():

    markdown = """
| Year | Revenue |
|------|----------|
|2024|100|
|2025|120|
"""

    parser = TableParser()

    tables = parser.parse(markdown)

    assert len(tables) == 1

    table = tables[0]

    assert table.headers == [
        "Year",
        "Revenue",
    ]

    assert table.row_count == 2

    assert table.rows[0] == [
        "2024",
        "100",
    ]