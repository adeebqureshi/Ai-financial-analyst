from app.data.sec_document import SECDocument


def test_document():

    document = SECDocument(
        url="https://example.com",
        html="<html>Hello</html>",
    )

    assert document.length > 0