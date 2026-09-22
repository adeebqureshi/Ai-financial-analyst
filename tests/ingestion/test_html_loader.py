from app.ingestion.html_loader import HTMLLoader


def test_html_loader(tmp_path):

    html = tmp_path / "sample.html"

    html.write_text(
        """
        <html>
            <body>
                <h1>Apple Inc.</h1>
                <p>Revenue increased 15%.</p>
            </body>
        </html>
        """,
        encoding="utf-8",
    )

    loader = HTMLLoader()

    document = loader.load(str(html))

    assert "Apple Inc." in document.text

    assert "Revenue increased 15%." in document.text

    assert document.metadata.source == "html"

    assert document.metadata.filename == "sample.html"

    assert document.metadata.mime_type == "text/html"