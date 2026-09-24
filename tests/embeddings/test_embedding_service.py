from unittest.mock import MagicMock, patch

import pytest

from app.core.exceptions import RetrievalError
from app.embeddings.embedding_service import EmbeddingService, _expected_dimension


class _StubModel:
    def __init__(self, vector):
        self._vector = vector

    def embed(self, text):
        return MagicMock(vector=self._vector)


def _full_vector(value: float = 0.5) -> list[float]:
    return [value] * _expected_dimension()


@patch("app.embeddings.embedding_service._get_model")
def test_embed_text(mock_get_model):
    expected = _expected_dimension()
    mock_get_model.return_value = _StubModel([1.0] * expected)
    service = EmbeddingService()
    vector = service.embed_text("Apple")
    assert vector == [1.0] * expected


@patch("app.embeddings.embedding_service._get_model")
def test_embed_documents(mock_get_model):
    expected = _expected_dimension()
    mock_get_model.return_value = _StubModel([0.5] * expected)
    service = EmbeddingService()
    vectors = service.embed_documents(["Apple", "Microsoft"])
    assert len(vectors) == 2
    assert all(len(v) == expected for v in vectors)


@patch("app.embeddings.embedding_service._get_model")
def test_embed_text_rejects_dimension_mismatch(mock_get_model):
    mock_get_model.return_value = _StubModel([1.0, 2.0])  # wrong dimension
    service = EmbeddingService()
    with pytest.raises(RetrievalError) as exc_info:
        service.embed_text("Apple")
    assert exc_info.value.error_code == "EMBEDDING_DIMENSION_MISMATCH"


@patch("app.embeddings.embedding_service._get_model")
def test_embed_text_rejects_zero_vector(mock_get_model):
    mock_get_model.return_value = _StubModel(_full_vector(0.0))
    service = EmbeddingService()
    with pytest.raises(RetrievalError) as exc_info:
        service.embed_text("Apple")
    assert exc_info.value.error_code == "EMBEDDING_FAILED"


@patch("app.embeddings.embedding_service._get_model")
def test_embed_documents_wraps_model_failure(mock_get_model):
    mock_get_model.side_effect = RuntimeError("model download failed")
    service = EmbeddingService()
    with pytest.raises(RetrievalError) as exc_info:
        service.embed_documents(["Apple"])
    assert exc_info.value.error_code == "EMBEDDING_FAILED"