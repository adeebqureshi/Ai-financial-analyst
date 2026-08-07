from app.parsing.metric import FinancialMetric


def test_numeric():

    metric = FinancialMetric(
        name="Revenue",
        value="$1,250.50",
        source="regex",
    )

    assert metric.numeric == 1250.50


def test_invalid():

    metric = FinancialMetric(
        name="Revenue",
        value="N/A",
        source="regex",
    )

    assert metric.numeric is None