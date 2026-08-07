import pytest

from app.llm.exceptions import AuthenticationError
from app.llm.exceptions import LLMError
from app.llm.exceptions import ProviderError
from app.llm.exceptions import RateLimitError
from app.llm.exceptions import TimeoutError


def test_inheritance():

    assert issubclass(ProviderError, LLMError)
    assert issubclass(AuthenticationError, ProviderError)
    assert issubclass(RateLimitError, ProviderError)
    assert issubclass(TimeoutError, ProviderError)


def test_raise():

    with pytest.raises(ProviderError):
        raise ProviderError("provider failed")


def test_auth():

    with pytest.raises(AuthenticationError):
        raise AuthenticationError()


def test_rate_limit():

    with pytest.raises(RateLimitError):
        raise RateLimitError()


def test_timeout():

    with pytest.raises(TimeoutError):
        raise TimeoutError()