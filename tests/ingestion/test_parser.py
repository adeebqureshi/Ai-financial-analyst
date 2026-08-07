from app.ingestion.parser import PlainTextParser


def test_parser(tmp_path):

    file = tmp_path / "company.txt"

    file.write_text("Apple Revenue Growth")

    parser = PlainTextParser()

    document = parser.parse(str(file))

    assert document.metadata.filename == "company.txt"

    assert document.word_count == 3