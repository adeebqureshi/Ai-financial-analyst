from app.rag.embedding import Embedding


def test_embedding():

    embedding = Embedding(
        text="Revenue",
        vector=[0.1, 0.2, 0.3],
    )

    assert embedding.dimension == 3

    assert embedding.text == "Revenue"