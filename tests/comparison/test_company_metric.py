from app.comparison.company_metric import CompanyMetric


def test_metric():

    metric = CompanyMetric(
        "Apple",
        10,
    )

    assert metric.value == 10