from app.parsing.chunk import Chunk


def test_chunk():

    chunk = Chunk(
        id=0,
        text="Revenue increased significantly.",
        section="Revenue",
    )

    assert chunk.word_count == 3