from app.parsing.chunker import Chunker
from app.parsing.section import Section


def test_chunker():

    section = Section(
        title="Revenue",
        content=" ".join(["word"] * 250),
    )

    chunker = Chunker(
        chunk_size=100,
    )

    chunks = chunker.chunk([section])

    assert len(chunks) == 3

    assert chunks[0].section == "Revenue"

    assert chunks[0].word_count == 100

    assert chunks[2].word_count == 50