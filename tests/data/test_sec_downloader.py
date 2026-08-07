from app.data.sec_downloader import SECDownloader


def test_downloader():

    downloader = SECDownloader()

    document = downloader.download(
        "https://www.sec.gov"
    )

    assert document.length > 0