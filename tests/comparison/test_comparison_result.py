from app.comparison.company_metric import CompanyMetric
from app.comparison.comparison_result import ComparisonResult


def test_result():

    result = ComparisonResult(
        metric="Revenue",
        companies=[
            CompanyMetric("Apple", 10),
            CompanyMetric("Microsoft", 5),
        ],
    )

    assert result.winner.company == "Apple"