from app.finance.altman import AltmanZScore


def test_safe():

    score = AltmanZScore(
        score=3.4,
    )

    assert score.zone == "Safe"


def test_distress():

    score = AltmanZScore(
        score=1.2,
    )

    assert score.zone == "Distress"