from app.workflow.metrics import WorkflowMetrics


def test_metrics():

    metrics = WorkflowMetrics()

    metrics.increment()

    metrics.increment()

    assert metrics.executed == 2