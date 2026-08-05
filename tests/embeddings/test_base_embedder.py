from app.embeddings.base_embedder import BaseEmbedder


class DummyEmbedder(BaseEmbedder):

    def embed_text(self, text: str) -> list[float]:
        return [1.0, 2.0, 3.0]

    def embed_documents(
        self,
        documents: list[str],
    ) -> list[list[float]]:
        return [[1.0, 2.0, 3.0] for _ in documents]


def test_embed_text():

    embedder = DummyEmbedder()

    vector = embedder.embed_text("Apple")

    assert len(vector) == 3


def test_embed_documents():

    embedder = DummyEmbedder()

    vectors = embedder.embed_documents(
        [
            "Apple",
            "Microsoft",
        ]
    )

    assert len(vectors) == 2

    assert len(vectors[0]) == 3