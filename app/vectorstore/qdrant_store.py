from __future__ import annotations
import os
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    FilterSelector,
    MatchValue,
    PointIdsList,
    PointStruct,
    VectorParams,
)
import math

from app.core.exceptions import RetrievalError
from app.core.logging import get_logger
from app.vectorstore.base_vector_store import BaseVectorStore

_DEFAULT_COLLECTION = "financial_documents"
_DEFAULT_VECTOR_SIZE = 384
_DEFAULT_GRPC_PORT = 6334
_client: QdrantClient | None = None
logger = get_logger(__name__)


def _settings_dim() -> int | None:
    try:
        from app.core.config import get_settings

        dim = int(getattr(get_settings(), "embedding_dimension", 0) or 0)
        return dim or None
    except Exception:
        return None


def _settings_value(name: str) -> str | None:
    try:
        from app.core.config import get_settings

        value = getattr(get_settings(), name, "") or ""
    except Exception:
        value = ""
    return value.strip() or (os.getenv(name) or None)


def _reset_shared_client_for_tests() -> None:
    global _client
    try:
        if _client is not None:
            _client.close()
    except Exception:
        pass
    _client = None


def _get_shared_client(
    url: str | None,
    api_key: str | None,
) -> QdrantClient:
    """Return the process-wide Qdrant client, preferring the gRPC transport.

    Measured on the local stack: a 121-point scroll costs ~48 ms over gRPC but
    ~2,050 ms over REST, and retrieval refreshes the index on every query, so
    the transport choice dominated end-to-end latency. gRPC is only used when
    the client and server both support it; otherwise we transparently fall back
    to the previous REST behaviour.
    """
    global _client
    if _client is None:
        if url:
            try:
                _client = QdrantClient(
                    url=url,
                    api_key=api_key,
                    prefer_grpc=True,
                )
            except Exception as exc:  # pragma: no cover - environment dependent
                logger.warning(
                    "Qdrant gRPC transport unavailable (%s); using REST.",
                    exc,
                )
                _client = QdrantClient(url=url, api_key=api_key)
        else:
            # No URL configured. An in-memory client starts empty and answers
            # every query with zero results, which reads as "your documents
            # have no relevant evidence" rather than "storage is not
            # configured", so make the substitution loud.
            logger.warning(
                "No Qdrant URL configured (QDRANT_URL unset); using an empty "
                "in-memory store. Persisted documents are NOT searchable and "
                "nothing will be retained across restarts.",
            )
            _client = QdrantClient(":memory:")
    return _client


class QdrantStore(BaseVectorStore):
    def __init__(
        self,
        collection_name: str | None = None,
        vector_size: int | None = None,
        url: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self.collection_name = (
            collection_name
            or _settings_value("qdrant_collection")
            or os.getenv("QDRANT_COLLECTION")
            or _DEFAULT_COLLECTION
        )
        self.vector_size = (
            vector_size
            or _settings_dim()
            or int(os.getenv("EMBEDDING_DIMENSION", _DEFAULT_VECTOR_SIZE))
        )
        self._url = url or _settings_value("qdrant_url")
        self._api_key = api_key or _settings_value("qdrant_api_key")
        self._client_override = None
        try:
            self._ensure_collection()
        except RetrievalError:
            raise
        except Exception as exc:
            logger.warning("Qdrant initialization failed: %s", exc)
            raise RetrievalError(
                "Document storage is temporarily unavailable.",
                error_code="VECTOR_STORE_UNAVAILABLE",
            ) from exc

    @property
    def client(self) -> QdrantClient:
        if self._client_override is not None:
            return self._client_override
        return _get_shared_client(self._url, self._api_key)

    def _call(self, operation: str, function, *args, **kwargs):
        try:
            return function(*args, **kwargs)
        except RetrievalError:
            raise
        except (ConnectionError, TimeoutError, OSError) as exc:
            logger.warning("Qdrant %s failed: %s", operation, exc)
            raise RetrievalError(
                "Document search is temporarily unavailable.",
                error_code="VECTOR_STORE_UNAVAILABLE",
            ) from exc
        except Exception as exc:
            message = str(exc).lower()
            if any(term in message for term in ("connection", "timeout", "unavailable", "refused")):
                logger.warning("Qdrant %s failed: %s", operation, exc)
                raise RetrievalError(
                    "Document search is temporarily unavailable.",
                    error_code="VECTOR_STORE_UNAVAILABLE",
                ) from exc
            raise

    def _ensure_collection(self) -> None:
        try:
            return self._collection_check()
        except RetrievalError:
            raise
        except Exception as exc:
            # `get_collections` already failed by the time this runs, so a
            # connection error here means the server is unreachable, not that
            # the collection is missing. Naming the configured endpoint makes
            # a stopped local Qdrant obvious instead of looking like a data
            # problem. Only the endpoint is logged, never the API key.
            logger.warning(
                "Qdrant is unreachable at %s (collection=%s, gRPC port %s "
                "preferred, REST fallback available): %s",
                self._url or "<in-memory>",
                self.collection_name,
                _DEFAULT_GRPC_PORT,
                exc,
            )
            raise RetrievalError(
                "Document storage is temporarily unavailable.",
                error_code="VECTOR_STORE_UNAVAILABLE",
            ) from exc

    def _collection_check(self) -> None:
        collections = {
            c.name
            for c in self.client.get_collections().collections
        }
        if self.collection_name not in collections:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE,
                ),
            )
            return
        info = self.client.get_collection(self.collection_name)
        stored_size = getattr(
            getattr(info.config.params, "vectors", None),
            "size",
            None,
        )
        if stored_size is not None and stored_size != self.vector_size:
            raise ValueError(
                f"Collection '{self.collection_name}' exists with vector size "
                f"{stored_size} but {self.vector_size} is required."
            )

    @staticmethod
    def _tenant_filter(tenant_id: str) -> FieldCondition:
        if not isinstance(tenant_id, str) or not tenant_id:
            raise RetrievalError(
                "Tenant context is required for document retrieval.",
                error_code="TENANT_REQUIRED",
            )
        return FieldCondition(
            key="tenant_id",
            match=MatchValue(value=tenant_id),
        )

    @staticmethod
    def _combined_filter(
        document_id: str | None,
        tenant_id: str,
    ) -> Filter:
        filters = [QdrantStore._tenant_filter(tenant_id)]
        if document_id:
            filters.append(
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=document_id),
                )
            )
        return Filter(must=filters)

    def upsert(
        self,
        ids: list[int | str],
        vectors: list[list[float]],
        payloads: list[dict],
    ) -> None:
        batch_size = self._upsert_batch_size()
        if batch_size <= 0 or len(ids) <= batch_size:
            self._upsert_points(ids, vectors, payloads)
            return
        # Large documents (e.g. 360-page reports) produce hundreds of points.
        # One giant upsert risks payload/timeout limits, so split into
        # bounded batches while keeping each call server-efficient.
        for start in range(0, len(ids), batch_size):
            end = start + batch_size
            self._upsert_points(
                ids[start:end],
                vectors[start:end],
                payloads[start:end],
            )

    @staticmethod
    def _upsert_batch_size() -> int:
        try:
            from app.core.config import get_settings

            size = int(
                getattr(get_settings(), "qdrant_upsert_batch_size", 256) or 256
            )
        except Exception:
            return 256
        return max(1, min(size, 4096))

    def _upsert_points(
        self,
        ids: list[int | str],
        vectors: list[list[float]],
        payloads: list[dict],
    ) -> None:
        points = []
        for idx, vector, payload in zip(
            ids,
            vectors,
            payloads,
        ):
            points.append(
                PointStruct(
                    id=idx,
                    vector=vector,
                    payload=payload,
                )
            )
        self._call(
            "upsert",
            self.client.upsert,
            collection_name=self.collection_name,
            points=points,
        )

    @staticmethod
    def _valid_point(point) -> bool:
        point_id = getattr(point, "id", None)
        if not isinstance(point_id, (int, str)) or isinstance(point_id, bool):
            return False
        payload = getattr(point, "payload", None)
        if not isinstance(payload, dict):
            return False
        if "text" in payload and not isinstance(payload["text"], str):
            return False
        if "chunk_id" in payload and not isinstance(payload["chunk_id"], str):
            return False
        score = getattr(point, "score", None)
        return score is None or (isinstance(score, (int, float)) and math.isfinite(score))

    def search(
        self,
        vector: list[float],
        limit: int = 5,
        document_id: str | None = None,
        owner_id: str | None = None,
    ):
        query_filter = self._combined_filter(document_id, owner_id)
        result = self._call(
            "search",
            self.client.query_points,
            collection_name=self.collection_name,
            query=vector,
            limit=limit,
            query_filter=query_filter,
        )
        points = getattr(result, "points", None)
        if not isinstance(points, list):
            raise RetrievalError(
                "Document search returned an invalid response.",
                error_code="VECTOR_STORE_INVALID_RESPONSE",
            )
        return [point for point in points if self._valid_point(point)]

    def delete(
        self,
        ids: list[int | str],
    ) -> None:
        self._call(
            "delete",
            self.client.delete,
            collection_name=self.collection_name,
            points_selector=PointIdsList(points=list(ids)),
        )

    def delete_by_document_id(
        self,
        document_id: str,
        owner_id: str | None = None,
    ) -> None:
        self._call(
            "delete_by_document_id",
            self.client.delete,
            collection_name=self.collection_name,
            points_selector=FilterSelector(
                filter=self._combined_filter(document_id, owner_id),
            ),
        )

    def get_all(
        self,
        limit: int = 10_000,
        owner_id: str | None = None,
    ):
        points, _ = self._call(
            "get_all",
            self.client.scroll,
            collection_name=self.collection_name,
            limit=limit,
            scroll_filter=self._combined_filter(None, owner_id),
        )
        return points

    def count(self) -> int:
        result = self._call(
            "count",
            self.client.count,
            collection_name=self.collection_name,
        )
        return result.count
