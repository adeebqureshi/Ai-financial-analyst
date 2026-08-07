from app.ingestion.xbrl_loader import XBRLLoader


def test_xbrl_loader(tmp_path):

    xml = tmp_path / "sample.xml"

    xml.write_text(
        """
        <xbrl>
            <Revenue>1000000</Revenue>
            <NetIncome>250000</NetIncome>
        </xbrl>
        """,
        encoding="utf-8",
    )

    loader = XBRLLoader()

    document = loader.load(str(xml))

    assert "1000000" in document.text

    assert "250000" in document.text

    assert document.metadata.source == "xbrl"

    assert document.metadata.filename == "sample.xml"

    assert document.metadata.mime_type == "application/xml"