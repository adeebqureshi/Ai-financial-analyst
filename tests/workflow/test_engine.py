from app.workflow.engine import WorkflowEngine


def test_engine():

    engine = WorkflowEngine()

    result = engine.run(
        "Apple valuation",
    )

    assert result.success

    assert result.completed_steps == 5