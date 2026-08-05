from app.parsers.chunker import Chunker


def test_chunk_document():

    parser = Chunker(
        chunk_size=5,
        overlap=1,
    )

    sections = {
        "Business":
        "one two three four five six seven eight nine ten"
    }

    chunks = parser.chunk_document(sections)

    assert len(chunks) == 3

    assert chunks[0].section == "Business"

    assert chunks[0].chunk_id == 0

    assert chunks[1].chunk_id == 1

    assert chunks[2].chunk_id == 2