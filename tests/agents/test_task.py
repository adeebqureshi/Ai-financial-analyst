from app.agents.task import Task


def test_task():

    task = Task(
        name="Generate Report",
        description="Create investment report.",
    )

    assert task.short_name == "generate_report"