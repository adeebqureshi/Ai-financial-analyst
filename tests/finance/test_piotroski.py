from app.finance.piotroski import PiotroskiScore


def test_rating():

    score = PiotroskiScore(
        score=8,
    )

    assert score.rating == "Strong"


def test_weak():

    score = PiotroskiScore(
        score=3,
    )

    assert score.rating == "Weak"