from app.agents.quant import QuantAgent


def test_quant():

    agent = QuantAgent()

    result = agent.analyze(
        "Apple",
    )

    assert result.company == "Apple"

    assert result.metric_count == 7

    assert result.metrics["current_ratio"] == 2.0