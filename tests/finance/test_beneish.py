from app.finance.beneish import BeneishMScore


def test_manipulator():

    score = BeneishMScore(
        score=-1.5,
    )

    assert score.likely_manipulator


def test_not_manipulator():

    score = BeneishMScore(
        score=-2.5,
    )

    assert not score.likely_manipulator