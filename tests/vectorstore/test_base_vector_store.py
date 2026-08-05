from app.vectorstore.base_vector_store import BaseVectorStore


class DummyStore(BaseVectorStore):

    def upsert(
        self,
        ids,
        vectors,
        payloads,
    ):
        return None

    def search(
        self,
        vector,
        limit=5,
    ):
        return []


def test_store():

    store = DummyStore()

    assert store.search([1.0]) == []