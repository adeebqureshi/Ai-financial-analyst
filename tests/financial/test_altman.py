import pytest

from app.financial.altman import AltmanZScore


def test_altman_score():

    score = AltmanZScore.calculate(
        working_capital=500,
        retained_earnings=1200,
        ebit=900,
        market_value_equity=6000,
        total_liabilities=3000,
        sales=8000,
        total_assets=10000,
    )

    assert score == pytest.approx(2.525, abs=1e-6)


def test_safe_zone():

    assert AltmanZScore.interpretation(3.5) == "SAFE"


def test_grey_zone():

    assert AltmanZScore.interpretation(2.5) == "GREY"


def test_distress_zone():

    assert AltmanZScore.interpretation(1.2) == "DISTRESS"


def test_invalid_assets():

    with pytest.raises(ValueError):

        AltmanZScore.calculate(
            working_capital=100,
            retained_earnings=100,
            ebit=100,
            market_value_equity=100,
            total_liabilities=100,
            sales=100,
            total_assets=0,
        )