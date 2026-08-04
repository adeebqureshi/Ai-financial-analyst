from app.ingestion.storage.storage_service import StorageService


def test_save_and_load_market_data():

    storage = StorageService()

    data = {
        "ticker": "AAPL",
        "price": 200,
    }

    storage.save_market_data(
        "AAPL",
        data,
    )

    loaded = storage.load_market_data("AAPL")

    assert loaded == data


def test_save_and_load_metadata():

    storage = StorageService()

    metadata = {
        "company": "Apple",
    }

    storage.save_metadata(
        "apple.json",
        metadata,
    )

    loaded = storage.load_metadata(
        "apple.json",
    )

    assert loaded == metadata


def test_save_and_load_sec():

    storage = StorageService()

    html = "<html>Hello SEC</html>"

    storage.save_sec_filing(
        ticker="AAPL",
        year=2024,
        form_type="10-K",
        html=html,
    )

    loaded = storage.load_sec_filing(
        "AAPL",
        2024,
        "10-K",
    )

    assert loaded == html