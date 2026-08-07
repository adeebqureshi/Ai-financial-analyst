from unittest.mock import MagicMock

import pytest

from app.llm.exceptions import ProviderError
from app.llm.exceptions import TimeoutError
from app.llm.retry import RetryPolicy


def test_retry_success():

    retry = RetryPolicy(max_attempts=3, base_delay=0)

    func = MagicMock(return_value="OK")

    assert retry.execute(func) == "OK"

    assert func.call_count == 1


def test_retry_after_timeout():

    retry = RetryPolicy(max_attempts=3, base_delay=0)

    func = MagicMock(
        side_effect=[
            TimeoutError(),
            "SUCCESS",
        ]
    )

    assert retry.execute(func) == "SUCCESS"

    assert func.call_count == 2


def test_retry_exhausted():

    retry = RetryPolicy(max_attempts=3, base_delay=0)

    func = MagicMock(side_effect=TimeoutError())

    with pytest.raises(TimeoutError):
        retry.execute(func)

    assert func.call_count == 3


def test_provider_error_not_retried():

    retry = RetryPolicy(max_attempts=3, base_delay=0)

    func = MagicMock(side_effect=ProviderError())

    with pytest.raises(ProviderError):
        retry.execute(func)

    assert func.call_count == 1