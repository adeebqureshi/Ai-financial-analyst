import pytest

from app.llm.exceptions import ProviderError
from app.llm.exceptions import RateLimitError
from app.llm.exceptions import TimeoutError
from app.llm.retry import RetryPolicy


def test_success():

    policy = RetryPolicy()

    result = policy.execute(lambda: "OK")

    assert result == "OK"


def test_retry_timeout():

    policy = RetryPolicy(max_attempts=3, base_delay=0)

    count = 0

    def func():
        nonlocal count
        count += 1

        if count < 3:
            raise TimeoutError()

        return "SUCCESS"

    assert policy.execute(func) == "SUCCESS"

    assert count == 3


def test_retry_rate_limit():

    policy = RetryPolicy(max_attempts=3, base_delay=0)

    count = 0

    def func():
        nonlocal count
        count += 1

        if count < 3:
            raise RateLimitError()

        return "SUCCESS"

    assert policy.execute(func) == "SUCCESS"

    assert count == 3


def test_provider_error_not_retried():

    policy = RetryPolicy(max_attempts=5, base_delay=0)

    count = 0

    def func():
        nonlocal count
        count += 1
        raise ProviderError()

    with pytest.raises(ProviderError):
        policy.execute(func)

    assert count == 1


def test_timeout_failure():

    policy = RetryPolicy(max_attempts=3, base_delay=0)

    def func():
        raise TimeoutError()

    with pytest.raises(TimeoutError):
        policy.execute(func)


def test_rate_limit_failure():

    policy = RetryPolicy(max_attempts=3, base_delay=0)

    def func():
        raise RateLimitError()

    with pytest.raises(RateLimitError):
        policy.execute(func)