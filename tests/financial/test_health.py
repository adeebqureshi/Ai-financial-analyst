from app.financial.health import FinancialHealth


def test_excellent():

    score = FinancialHealth.score(
        piotroski=9,
        altman=3.5,
        beneish=-2.5,
    )

    assert score == 100

    assert FinancialHealth.rating(score) == "EXCELLENT"


def test_good():

    score = FinancialHealth.score(
        piotroski=6,
        altman=2.4,
        beneish=-2.2,
    )

    assert score == 75

    assert FinancialHealth.rating(score) == "GOOD"


def test_fair():

    score = FinancialHealth.score(
        piotroski=4,
        altman=1.7,
        beneish=-1.5,
    )

    assert score == 30

    assert FinancialHealth.rating(score) == "POOR"