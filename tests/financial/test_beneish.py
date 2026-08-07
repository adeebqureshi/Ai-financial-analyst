import pytest

from app.financial.beneish import BeneishMScore


def test_beneish_score():

    score = BeneishMScore.calculate(
        dsri=1.10,
        gmi=1.05,
        aqi=1.00,
        sgi=1.08,
        depi=0.98,
        sgai=1.02,
        lvgi=1.01,
        tata=0.03,
    )

    assert score == pytest.approx(-2.15888, abs=1e-5)


def test_low_risk():

    assert BeneishMScore.interpretation(-2.5) == "LOW_RISK"


def test_high_risk():

    assert BeneishMScore.interpretation(-1.5) == "HIGH_RISK"