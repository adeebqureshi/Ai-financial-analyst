from app.rag.embedding import Embedding
from app.rag.embedding_model import EmbeddingModel


class DummyEmbeddingModel(EmbeddingModel):

    def embed(
        self,
        text: str,
    ) -> Embedding:

        return Embedding(
            text=text,
            vector=[1.0, 2.0, 3.0],
        )


def test_model():

    model = DummyEmbeddingModel()

    embedding = model.embed("Apple")

    assert embedding.dimension == 3

    assert embedding.text == "Apple"