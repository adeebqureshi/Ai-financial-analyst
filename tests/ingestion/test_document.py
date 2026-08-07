from app.ingestion.document import FinancialDocument
from app.ingestion.metadata import DocumentMetadata


def test_document():

    doc = FinancialDocument(
        text="Apple revenue increased significantly.",
        metadata=DocumentMetadata(
            source="sec",
            filename="10k.html",
        ),
    )

    assert doc.word_count == 4
    assert not doc.is_empty


def test_empty():

    doc = FinancialDocument(
        text="",
        metadata=DocumentMetadata(
            source="pdf",
            filename="empty.pdf",
        ),
    )

    assert doc.is_empty