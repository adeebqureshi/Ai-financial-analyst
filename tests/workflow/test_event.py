from app.workflow.event import WorkflowEvent


def test_event():

    event = WorkflowEvent(
        node="planner",
        message="Started",
    )

    assert event.node == "planner"

    assert event.message == "Started"