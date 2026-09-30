from __future__ import annotations
import threading
from sentence_transformers import CrossEncoder
_RERANKER_LOCK = threading.Lock()
_RERANKERS: dict[str, "Reranker"] = {}
class Reranker:
    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    ) -> None:
        self.model = CrossEncoder(model_name)
    def rerank(
        self,
        query: str,
        documents: list[str],
    ) -> list[tuple[str, float]]:
        pairs = [
            (query, doc)
            for doc in documents
        ]
        scores = self.model.predict(pairs)
        ranked = sorted(
            zip(documents, scores),
            key=lambda x: x[1],
            reverse=True,
        )
        return ranked
def get_reranker(
    model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
) -> Reranker:
    """Return a process-wide reranker, mirroring the embedding-model cache.

    A ``RetrievalEngine`` is built per request, so constructing the
    cross-encoder inside ``Reranker.__init__`` re-loaded the model on every
    search. The model is immutable after construction and only used for
    inference, so a single instance per process is safe and far cheaper.
    """
    instance = _RERANKERS.get(model_name)
    if instance is None:
        with _RERANKER_LOCK:
            instance = _RERANKERS.get(model_name)
            if instance is None:
                instance = Reranker(model_name)
                _RERANKERS[model_name] = instance
    return instance
