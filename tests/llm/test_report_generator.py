from types import SimpleNamespace
from unittest.mock import MagicMock
from unittest.mock import patch

from app.llm.models import LLMResponse
from app.llm.report_generator import ReportGenerator


@patch("app.llm.report_generator.OpenAIClient")
def test_report_generator(mock_client):

    client = MagicMock()

    client.generate.return_value = LLMResponse(
        text="FINAL_REPORT",
        model="mock",
    )

    mock_client.return_value = client

    result = {
        "company": SimpleNamespace(
            name="Apple Inc.",
            ticker="AAPL",
        ),
        "market": SimpleNamespace(
            current_price=200,
            currency="USD",
        ),
        "analysis": SimpleNamespace(
            intrinsic_value=250,
            upside=20,
            recommendation="BUY",
            health_score=95,
            health_rating="EXCELLENT",
            piotroski_score=9,
            altman_score=3.5,
            beneish_score=-2.4,
        ),
    }

    generator = ReportGenerator()

    report = generator.generate(
        query="Should I buy Apple?",
        context="Revenue increased.",
        result=result,
    )

    assert report == "FINAL_REPORT"

    client.generate.assert_called_once()