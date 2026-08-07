from app.ingestion.metadata import DocumentMetadata


def test_metadata():

    meta = DocumentMetadata(
        source="sec",
        filename="10k.html",
    )

    assert meta.source == "sec"
    assert meta.filename == "10k.html"


def test_extra():

    meta = DocumentMetadata(
        source="pdf",
        filename="a.pdf",
    )

    meta.extra["year"] = "2025"

    assert meta.extra["year"] == "2025"