from __future__ import annotations
import logging
from app.core.config import get_settings
from app.rag.sentence_transformer_model import SentenceTransformerEmbeddingModel

logger = logging.getLogger(__name__)

_model: SentenceTransformerEmbeddingModel | None = None

def _get_model() -> SentenceTransformerEmbeddingModel:
    global _model
    if _model is None:
        settings = get_settings()
        model_name = getattr(settings, "embedding_model", "BAAI/bge-small-en-v1.5")
        logger.info("Loading local embedding model: %s", model_name)
        _model = SentenceTransformerEmbeddingModel(model_name)
    return _model

class EmbeddingService:
    def embed_text(self, text: str) -> list[float]:
        try:
            return _get_model().embed(text).vector
        except Exception as exc:
            logger.warning("Local embedding failed (%s)", exc)
            return [0.0] * 384

    def embed_documents(self, documents: list[str]) -> list[list[float]]:
        try:
            model = _get_model()
            return [model.embed(doc).vector for doc in documents]
        except Exception as exc:
            logger.warning("Local batch embedding failed (%s)", exc)
            return [[0.0] * 384 for _ in documents]