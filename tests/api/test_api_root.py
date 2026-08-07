from app.api.root import RootService


def test_root():

    result = RootService.info()

    assert result["application"] == "AI Financial Analyst"
    assert result["status"] == "running"
    assert result["version"] == "1.0.0"