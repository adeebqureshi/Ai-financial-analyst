from app.rag.sentence_transformer_model import (
    SentenceTransformerEmbeddingModel,
)


def test_embedding():

    model = SentenceTransformerEmbeddingModel()

    embedding = model.embed(
        "Apple revenue increased."
    )

    assert embedding.dimension > 300

    assert embedding.text == "Apple revenue increased."