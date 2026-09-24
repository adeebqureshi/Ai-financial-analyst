from __future__ import annotations
import logging
from app.core.config import get_settings
from app.core.exceptions import RetrievalError
from app.rag.sentence_transformer_model import SentenceTransformerEmbeddingModel

logger = logging.getLogger(__name__)

_model: SentenceTransformerEmbeddingModel | None = None


def _expected_dimension() -> int:
    settings = get_settings()
    dim = int(getattr(settings, "embedding_dimension", 384) or 384)
    return dim


def _get_model() -> SentenceTransformerEmbeddingModel:
    global _model
    if _model is None:
        settings = get_settings()
        model_name = getattr(settings, "embedding_model", "all-MiniLM-L6-v2")
        logger.info("Loading local embedding model: %s", model_name)
        _model = SentenceTransformerEmbeddingModel(model_name)
    return _model


def _validate_vector(vector: list[float], expected: int) -> list[float]:
    if not isinstance(vector, list) or len(vector) != expected:
        raise RetrievalError(
            message=(
                "Embedding model produced an incompatible vector: "
                f"expected dimension {expected}, got "
                f"{len(vector) if isinstance(vector, list) else type(vector).__name__}. "
                "Check EMBEDDING_MODEL / EMBEDDING_DIMENSION configuration."
            ),
            error_code="EMBEDDING_DIMENSION_MISMATCH",
            details={"expected_dimension": expected},
        )
    if all(v == 0.0 for v in vector):
        raise RetrievalError(
            message="Embedding model returned a zero vector; refusing to index fake embeddings.",
            error_code="EMBEDDING_FAILED",
        )
    return vector


class EmbeddingService:
    def embed_text(self, text: str) -> list[float]:
        try:
            vector = _get_model().embed(text).vector
        except Exception as exc:
            logger.error("Local embedding failed: %s", exc)
            raise RetrievalError(
                message=f"Embedding generation failed: {exc}",
                error_code="EMBEDDING_FAILED",
            ) from exc
        return _validate_vector(list(vector), _expected_dimension())

    def embed_documents(self, documents: list[str]) -> list[list[float]]:
        try:
            model = _get_model()
            vectors = [list(model.embed(doc).vector) for doc in documents]
        except Exception as exc:
            logger.error("Local batch embedding failed: %s", exc)
            raise RetrievalError(
                message=f"Batch embedding generation failed: {exc}",
                error_code="EMBEDDING_FAILED",
            ) from exc
        expected = _expected_dimension()
        return [_validate_vector(vector, expected) for vector in vectors]


def _fallback_vector(*args, **kwargs):
    """Deterministic non-zero test vector (NOT used in production code).

    Production methods above always raise on failure. This helper exists only
    so unit tests can monkeypatch hermetic embeddings without downloads.
    """
    import hashlib

    def _vec_for_text(text: str, dim: int = 384) -> list[float]:
        seed = hashlib.sha256(text.encode("utf-8")).digest()
        vals = [(seed[i % len(seed)] / 255.0) - 0.5 for i in range(dim)]
        norm = sum(v * v for v in vals) ** 0.5 or 1.0
        return [v / norm for v in vals]

    # If the tests pass a list of strings (mocking embed_documents)
    if args and isinstance(args[0], list):
        return [_vec_for_text(str(t)) for t in args[0]]

    text = str(args[0]) if args else "test"
    return _vec_for_text(text)