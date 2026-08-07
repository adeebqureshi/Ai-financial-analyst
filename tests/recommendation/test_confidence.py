from app.recommendation.confidence import ConfidenceCalculator


def test_confidence():

    calc = ConfidenceCalculator()

    assert calc.calculate(80) == 0.8