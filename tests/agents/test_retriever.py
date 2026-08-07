from app.agents.retriever import RetrieverAgent
from app.rag.embedding import Embedding


def test_retrieve():

    agent = RetrieverAgent()

    docs = [
        Embedding(
            text="Apple revenue increased",
            vector=[1.0, 0.0],
        ),
        Embedding(
            text="Microsoft Azure",
            vector=[0.0, 1.0],
        ),
    ]

    result = agent.retrieve(
        "Apple revenue",
        docs,
    )

    assert result.count == 2

    assert "Apple revenue increased" in result.documents[0]