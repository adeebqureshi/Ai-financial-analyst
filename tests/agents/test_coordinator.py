from app.agents.coordinator import CoordinatorAgent
from app.rag.embedding import Embedding


def test_coordinator():

    coordinator = CoordinatorAgent()

    docs = [
        Embedding(
            text="Apple revenue increased",
            vector=[1.0, 0.0],
        ),
        Embedding(
            text="Operating margin improved",
            vector=[1.0, 0.1],
        ),
    ]

    result = coordinator.run(
        "Apple valuation",
        docs,
    )

    assert result.success

    assert result.report is not None