from app.infrastructure.chroma import ChromaManager


def test_chroma():

    chroma = ChromaManager()

    assert isinstance(
        chroma.heartbeat(),
        bool,
    )