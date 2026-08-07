from app.comparison.company_metric import CompanyMetric
from app.comparison.ranking import CompanyRanking


def test_rank():

    ranking = CompanyRanking()

    result = ranking.rank([
        CompanyMetric("A", 2),
        CompanyMetric("B", 5),
    ])

    assert result[0].company == "B"
