from app.api.version import VersionService


def test_version():

    result = VersionService.get()

    assert result["application"] == "AI Financial Analyst"
    assert result["version"] == "1.0.0"