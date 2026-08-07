from app.data.sec_document import SECDocument
from app.data.sec_service import SECService


def test_service():

    service = SECService()

    document = SECDocument(
        url="https://example.com",
        html="""
        <html>
            <body>
                Apple Revenue
            </body>
        </html>
        """,
    )

    text = service.extract_text(
        document,
    )

    assert "Apple" in text