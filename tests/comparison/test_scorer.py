from app.comparison.scorer import CompanyScorer


def test_score():

    scorer = CompanyScorer()

    assert scorer.score(10) == 10