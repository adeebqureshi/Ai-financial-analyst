from app.parsing.table import FinancialTable


def test_table():

    table = FinancialTable(
        title="Revenue",
        headers=["Year", "Revenue"],
        rows=[
            ["2024", "100"],
            ["2025", "120"],
        ],
    )

    assert table.row_count == 2

    assert table.column_count == 2