from unittest.mock import MagicMock
from unittest.mock import patch

from app.ingestion.sec_loader import SECLoader


@patch("app.ingestion.sec_loader.requests.get")
def test_sec_loader(mock_get):

    response = MagicMock()

    response.text = "<html>Apple 10-K</html>"

    response.raise_for_status.return_value = None

    mock_get.return_value = response

    loader = SECLoader()

    document = loader.load(
        "https://www.sec.gov/test.html"
    )

    assert document.metadata.source == "sec"

    assert "Apple" in document.text

    mock_get.assert_called_once()