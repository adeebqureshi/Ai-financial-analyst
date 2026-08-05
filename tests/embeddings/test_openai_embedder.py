from unittest.mock import MagicMock, patch

from app.embeddings.openai_embedder import OpenAIEmbedder


@patch("app.embeddings.openai_embedder.OpenAI")
def test_embed_text(mock_openai):

    mock_client = MagicMock()

    mock_openai.return_value = mock_client

    mock_client.embeddings.create.return_value.data = [
        MagicMock(
            embedding=[1.0, 2.0, 3.0]
        )
    ]

    embedder = OpenAIEmbedder()

    vector = embedder.embed_text(
        "Apple"
    )

    assert vector == [1.0, 2.0, 3.0]


@patch("app.embeddings.openai_embedder.OpenAI")
def test_embed_documents(mock_openai):

    mock_client = MagicMock()

    mock_openai.return_value = mock_client

    mock_client.embeddings.create.return_value.data = [
        MagicMock(embedding=[1.0]),
        MagicMock(embedding=[2.0]),
    ]

    embedder = OpenAIEmbedder()

    vectors = embedder.embed_documents(
        [
            "Apple",
            "Microsoft",
        ]
    )

    assert len(vectors) == 2