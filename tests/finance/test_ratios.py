from app.finance.ratios import FinancialRatios


def test_ratios():

    ratios = FinancialRatios(
        current_ratio=2.0,
        debt_to_equity=1.5,
        return_on_assets=0.12,
        return_on_equity=0.20,
        gross_margin=0.40,
        operating_margin=0.25,
        net_margin=0.18,
    )

    assert ratios.current_ratio == 2.0

    assert ratios.return_on_equity == 0.20