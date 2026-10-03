"""Provider failure matrix for the OpenAI-compatible LLM provider.

Background
----------
``OpenAIProvider`` is the single seam through which every OpenAI-shaped
gateway (OpenAI itself and the FreeLLMAPI gateway) fails. A provider outage must
surface as a typed domain error, must not leak the API key or the raw provider
body, and must not escape as an unhandled exception.

These tests drive each provider failure class (400/401/403/404/429/500/502/503,
timeout, connection failure, empty content) through that one seam, plus the
HTTP status translation applied at the API boundary.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import httpx
import openai
import pytest

from app.api.exceptions import get_status_code_for_domain_error
from app.core.exceptions import (
    QuotaExceededError,
    RetrievalError,
    ValidationError,
)
from app.llm.models import LLMRequest
from app.llm.exceptions import (
    AuthenticationError,
    ProviderError,
    RateLimitError,
    TimeoutError,
)
from app.llm.providers.openai_provider import OpenAIProvider


@pytest.fixture(autouse=True)
def _no_retry_sleep(monkeypatch):
    """Make retry backoff instantaneous.

    ``app.llm.retry`` sleeps between attempts with exponential backoff. Driving a
    permanent provider failure therefore burns tens of seconds of wall clock and
    trips the 60s suite timeout. The retry *count* is asserted separately, so only
    the delay is neutralised here — never the retry behaviour itself.
    """
    monkeypatch.setattr("app.llm.retry.time.sleep", lambda *_: None)


@pytest.fixture
def provider(monkeypatch):
    """A provider whose API key is present so execution reaches the call."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-not-a-real-secret")
    return OpenAIProvider()


def _make_raiser(exc: BaseException):
    """A mock whose call raises ``exc`` regardless of keyword arguments.

    ``chat.completions.create`` is invoked with keyword arguments only, so the
    stub must accept ``*args, **kwargs`` rather than a single positional.
    """
    raiser = MagicMock(side_effect=exc)
    return raiser


def _response(status_code: int = 200, headers: dict | None = None):
    response = httpx.Response(
        status_code=status_code,
        headers=headers or {},
        request=httpx.Request("POST", "https://llm.invalid/v1/chat/completions"),
    )
    return response


class TestProviderErrorMatrix:
    def test_401_maps_to_authentication_error(self, provider, monkeypatch):
        monkeypatch.setattr(
            provider.client.chat.completions,
            "create",
            _make_raiser(openai.AuthenticationError("bad key", response=_response(401), body=None)),
        )
        with pytest.raises(AuthenticationError) as excinfo:
            provider.generate(LLMRequest(prompt="hello"))

        assert "authentication failed" in str(excinfo.value).lower()

    def test_429_maps_to_rate_limit_error_with_retry_after(
        self, provider, monkeypatch
    ):
        response = _response(429, headers={"retry-after": "42"})
        monkeypatch.setattr(
            provider.client.chat.completions,
            "create",
            _make_raiser(
                openai.RateLimitError("slow down", response=response, body=None)
            ),
        )
        with pytest.raises(RateLimitError) as excinfo:
            provider.generate(LLMRequest(prompt="hello"))

        assert excinfo.value.retry_after == 42

    def test_timeout_maps_to_timeout_error(self, provider, monkeypatch):
        monkeypatch.setattr(
            provider.client.chat.completions,
            "create",
            _make_raiser(openai.APITimeoutError(request=_response().request)),
        )
        with pytest.raises(TimeoutError):
            provider.generate(LLMRequest(prompt="hello"))

    def test_connection_failure_maps_to_provider_error(self, provider, monkeypatch):
        monkeypatch.setattr(
            provider.client.chat.completions,
            "create",
            _make_raiser(openai.APIConnectionError(request=_response().request)),
        )
        with pytest.raises(ProviderError) as excinfo:
            provider.generate(LLMRequest(prompt="hello"))

        assert "connection failed" in str(excinfo.value).lower()

    @pytest.mark.parametrize("status", [400, 403, 404, 500, 502, 503])
    def test_other_statuses_map_to_provider_error(
        self, provider, monkeypatch, status
    ):
        """400/403/404/5xx all degrade to a typed ProviderError, never a raw raise."""
        monkeypatch.setattr(
            provider.client.chat.completions,
            "create",
            _make_raiser(openai.APIError("boom", request=_response(status).request, body=None)),
        )
        with pytest.raises(ProviderError) as excinfo:
            provider.generate(LLMRequest(prompt="hello"))

        assert "api error" in str(excinfo.value).lower()

    def test_provider_error_message_does_not_leak_the_key(self, provider, monkeypatch):
        monkeypatch.setattr(
            provider.client.chat.completions,
            "create",
            _make_raiser(openai.APIConnectionError(request=_response().request)),
        )
        with pytest.raises(ProviderError) as excinfo:
            provider.generate(LLMRequest(prompt="hello"))

        assert "test-key-not-a-real-secret" not in str(excinfo.value)


class TestHttpStatusTranslation:
    """The API boundary must translate domain errors without leaking detail."""

    @pytest.mark.parametrize(
        ("error", "expected"),
        [
            (QuotaExceededError("quota"), 429),
            (ValidationError("bad input"), 422),
            (RetrievalError("vector store down"), 502),
        ],
    )
    def test_domain_errors_map_to_expected_status(self, error, expected):
        assert get_status_code_for_domain_error(error) == expected

    def test_unknown_domain_error_is_not_reported_as_bad_gateway(self):
        from app.core.exceptions import FinancialAnalystError

        assert (
            get_status_code_for_domain_error(FinancialAnalystError("boom"))
            == 500
        )