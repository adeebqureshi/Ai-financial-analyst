from app.finance.dcf import DCFValuation


def test_dcf():

    valuation = DCFValuation(
        enterprise_value=1000,
        equity_value=900,
        intrinsic_value_per_share=9,
    )

    assert valuation.enterprise_value == 1000

    assert valuation.intrinsic_value_per_share == 9