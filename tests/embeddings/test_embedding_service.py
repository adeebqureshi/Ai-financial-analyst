from unittest.mock import MagicMock, patch

from app.embeddings.embedding_service import EmbeddingService


@patch("app.embeddings.embedding_service.OpenAIEmbedder")
def test_embed_text(mock_embedder):

    mock = MagicMock()

    mock.embed_text.return_value = [1.0, 2.0]

    mock_embedder.return_value = mock

    service = EmbeddingService()

    vector = service.embed_text("Apple")

    assert vector == [1.0, 2.0]


@patch("app.embeddings.embedding_service.OpenAIEmbedder")
def test_embed_documents(mock_embedder):

    mock = MagicMock()

    mock.embed_documents.return_value = [
        [1.0],
        [2.0],
    ]

    mock_embedder.return_value = mock

    service = EmbeddingService()

    vectors = service.embed_documents(
        [
            "Apple",
            "Microsoft",
        ]
    )

    assert len(vectors) == 2