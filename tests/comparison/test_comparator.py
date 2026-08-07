from app.comparison.company_metric import CompanyMetric
from app.comparison.comparator import CompanyComparator


def test_compare():

    comparator = CompanyComparator()

    result = comparator.compare(
        "Revenue",
        [
            CompanyMetric("Apple", 12),
            CompanyMetric("Microsoft", 8),
        ],
    )

    assert result.winner.company == "Apple"