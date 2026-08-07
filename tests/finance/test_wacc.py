from app.finance.wacc import WACC


def test_wacc():

    result = WACC(
        cost_of_equity=0.10,
        after_tax_cost_of_debt=0.04,
        wacc=0.08,
    )

    assert result.cost_of_equity == 0.10

    assert result.wacc == 0.08