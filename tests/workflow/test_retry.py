from app.workflow.retry import WorkflowRetry


def test_retry():

    retry = WorkflowRetry()

    counter = {
        "value": 0,
    }

    def func():

        counter["value"] += 1

        if counter["value"] < 2:
            raise ValueError

        return 10

    assert retry.execute(func) == 10