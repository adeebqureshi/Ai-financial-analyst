from app.parsing.metric_extractor import MetricExtractor


def test_extractor():

    text = """
Revenue: $1000000
Net Income: $250000
EPS: 3.42
"""

    extractor = MetricExtractor()

    metrics = extractor.extract(text)

    assert len(metrics) == 3

    assert metrics[0].name == "Revenue"
    assert metrics[0].numeric == 1000000

    assert metrics[1].name == "Net Income"

    assert metrics[2].name == "EPS"