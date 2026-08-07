from types import SimpleNamespace
from unittest.mock import MagicMock
from unittest.mock import patch

from app.api.router import AnalysisRouter
from app.api.schemas import AnalyzeRequest


@patch("app.api.router.ReportGenerator")
def test_router(mock_generator):

    generator = MagicMock()

    generator.generate.return_value = "BUY"

    mock_generator.return_value = generator

    router = AnalysisRouter()

    request = AnalyzeRequest(
        ticker="AAPL",
        query="Should I buy Apple?",
    )

    result = {
        "company": SimpleNamespace(
            name="Apple",
            ticker="AAPL",
        ),
        "market": SimpleNamespace(
            current_price=200,
            currency="USD",
        ),
        "analysis": SimpleNamespace(
            intrinsic_value=250,
            upside=25,
            recommendation="BUY",
            health_score=95,
            health_rating="EXCELLENT",
            piotroski_score=9,
            altman_score=3.5,
            beneish_score=-2.4,
        ),
    }

    response = router.analyze(
        request=request,
        result=result,
        context="Revenue increased.",
    )

    assert response.ticker == "AAPL"
    assert response.report == "BUY"