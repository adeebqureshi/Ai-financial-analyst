from app.api.health import HealthService


def test_health():

    result = HealthService.check()

    assert result["status"] == "healthy"
    assert result["service"] == "AI Financial Analyst"