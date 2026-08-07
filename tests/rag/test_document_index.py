from app.rag.document_index import DocumentIndex
from app.rag.embedding import Embedding


def test_index():

    index = DocumentIndex()

    index.add(
        Embedding(
            text="Apple",
            vector=[1.0],
        )
    )

    assert index.size == 1

    assert index.all()[0].text == "Apple"


def test_clear():

    index = DocumentIndex()

    index.add(
        Embedding(
            text="A",
            vector=[1.0],
        )
    )

    index.clear()

    assert index.size == 0