from app.workflow.history import WorkflowHistory


def test_history():

    history = WorkflowHistory()

    history.add("planner")

    history.add("retriever")

    assert history.count == 2