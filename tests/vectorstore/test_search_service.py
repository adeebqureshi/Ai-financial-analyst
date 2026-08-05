from unittest.mock import MagicMock, patch

from app.vectorstore.search_service import SearchService


@patch("app.vectorstore.search_service.EmbeddingService")
@patch("app.vectorstore.search_service.QdrantStore")
def test_search(mock_store, mock_embedder):

    embedder = MagicMock()
    embedder.embed_text.return_value = [0.1, 0.2, 0.3]
    mock_embedder.return_value = embedder

    store = MagicMock()
    store.search.return_value = ["result"]
    mock_store.return_value = store

    service = SearchService()

    results = service.search("Apple revenue")

    assert results == ["result"]

    embedder.embed_text.assert_called_once_with("Apple revenue")
    store.search.assert_called_once()