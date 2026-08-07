from app.rag.context import Context


def test_context():

    context = Context(
        text="Apple Revenue",
        chunk_count=1,
    )

    assert context.chunk_count == 1

    assert context.word_count == 2