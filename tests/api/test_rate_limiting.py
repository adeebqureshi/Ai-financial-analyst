"""
Rate Limiting Tests

Tests for per-user and IP-based rate limits on expensive endpoints.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import reset_rate_limits_for_testing
from app.schemas.analysis import FinancialStatementInput
from app.schemas.responses import (
    AnalyzeResponseData,
    ChatResponseData,
    CompanyData,
    HealthScoreData,
    MarketDataResponse,
    SearchResultData,
    ValuationResultData,
)
from app.api.dependencies.services import (
    get_analysis_service,
    get_chat_service,
    get_document_service,
    get_search_service,
)
from app.auth.dependencies import get_current_user
from app.api.rate_limiter import (
    HybridRateLimiter,
    LocalMemoryBackend,
    RateLimitConfig,
    RateLimitResult,
    get_endpoint_config,
    get_rate_limiter,
    reset_rate_limiter,
)
from app.auth.models import User
from app.core.config import Settings, get_settings
from app.main import app


client = TestClient(app)


def make_settings(**overrides: object) -> Settings:
    """Build an isolated immutable Settings copy for a test.

    The application ``Settings`` model is frozen (``model_config =
    SettingsConfigDict(frozen=True)``) so production configuration cannot be
    mutated at runtime. Tests must therefore never mutate the cached singleton
    returned by ``get_settings()``; instead they build their own frozen
    instance via ``model_copy(update=...)`` and inject it where needed
    (directly for unit tests, or through FastAPI dependency overrides for
    integration tests).
    """
    return get_settings().model_copy(update=overrides)  # type: ignore[arg-type]


def _chat_result() -> ChatResponseData:
    """Build a valid chat response payload for mocked services."""
    return ChatResponseData(message="Test response", ticker="AAPL")


def _analyze_result() -> AnalyzeResponseData:
    """Build a valid analyze response payload for mocked services."""
    return AnalyzeResponseData(
        ticker="AAPL",
        query="test",
        company=CompanyData(ticker="AAPL", name="Apple Inc."),
        market=MarketDataResponse(ticker="AAPL", current_price=150.0),
        statement=FinancialStatementInput(
            revenue=394328.0,
            operating_income=114301.0,
            net_income=96995.0,
            total_assets=352583.0,
            total_liabilities=279486.0,
            cash=30545.0,
            debt=111088.0,
            shares_outstanding=15431.0,
            free_cash_flow=99584.0,
        ),
        valuation=ValuationResultData(
            intrinsic_value=180.0,
            upside=0.2,
            recommendation="BUY",
            current_price=150.0,
            discount_rate=0.09,
        ),
        health=HealthScoreData(
            score=80,
            rating="GOOD",
            piotroski_score=7,
            altman_score=3.0,
            beneish_score=-2.0,
        ),
        recommendation="BUY",
    )


def _search_result() -> SearchResultData:
    """Build a valid search result payload for mocked services."""
    return SearchResultData(query="test", hits=[], total=0, retrieval_time_ms=1.0)


def install_dependency_overrides(
    settings: Settings,
    user: User | None,
    service: object,
    service_dependency: Callable[[], object],
) -> None:
    """Inject isolated test settings/user/service via FastAPI overrides.

    ``unittest.mock.patch`` cannot affect dependencies that FastAPI resolved
    at route-definition time, and mutating the frozen ``Settings`` singleton
    is forbidden. ``app.dependency_overrides`` is FastAPI's supported way to
    replace dependency callables per-test and keeps ``Settings(frozen=True)``
    intact.
    """
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[service_dependency] = lambda: service


class TestLocalMemoryBackend:
    """Tests for the local in-memory rate limiter backend."""

    def test_increment_and_get(self) -> None:
        backend = LocalMemoryBackend()
        key = "test:key"

        count1 = backend.increment(key, 60)
        assert count1 == 1

        count2 = backend.increment(key, 60)
        assert count2 == 2

        current = backend.get(key)
        assert current == 2

    def test_reset(self) -> None:
        backend = LocalMemoryBackend()
        key = "test:key"

        backend.increment(key, 60)
        backend.increment(key, 60)

        backend.reset(key)

        current = backend.get(key)
        assert current == 0

    def test_expiry(self) -> None:
        backend = LocalMemoryBackend()
        key = "test:key"

        backend.increment(key, 1)  # 1 second window

        assert backend.get(key) == 1

        time.sleep(1.1)

        assert backend.get(key) == 0

    def test_health_check(self) -> None:
        backend = LocalMemoryBackend()
        assert backend.health_check() is True

    def test_thread_safety(self) -> None:
        backend = LocalMemoryBackend()
        key = "test:concurrent"
        num_threads = 10
        increments_per_thread = 100

        def increment_many() -> None:
            for _ in range(increments_per_thread):
                backend.increment(key, 60)

        threads = []
        for _ in range(num_threads):
            t = threading.Thread(target=increment_many)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        final_count = backend.get(key)
        assert final_count == num_threads * increments_per_thread


class TestRateLimitConfig:
    """Tests for rate limit configurations."""

    def test_get_endpoint_config_chat(self) -> None:
        settings = get_settings()
        config = get_endpoint_config("chat", settings)

        assert config.requests_per_minute == settings.rate_limit_chat_per_minute
        assert config.requests_per_hour == settings.rate_limit_chat_per_hour
        assert config.key_prefix == "ratelimit:chat"

    def test_get_endpoint_config_analyze(self) -> None:
        settings = get_settings()
        config = get_endpoint_config("analyze", settings)

        assert config.requests_per_minute == settings.rate_limit_analyze_per_minute
        assert config.requests_per_hour == settings.rate_limit_analyze_per_hour
        assert config.key_prefix == "ratelimit:analyze"

    def test_get_endpoint_config_unknown_defaults(self) -> None:
        settings = get_settings()
        config = get_endpoint_config("unknown", settings)

        assert config.requests_per_minute == settings.rate_limit_default_per_minute
        assert config.requests_per_hour == settings.rate_limit_default_per_hour
        assert config.key_prefix == "ratelimit:default"


class TestHybridRateLimiter:
    """Tests for the hybrid rate limiter."""

    def setup_method(self) -> None:
        reset_rate_limiter()

    def teardown_method(self) -> None:
        reset_rate_limiter()

    def test_check_rate_limit_allowed(self) -> None:
        settings = make_settings(rate_limit_enabled=True)
        limiter = HybridRateLimiter(settings)
        config = RateLimitConfig(requests_per_minute=10, requests_per_hour=100)

        result = limiter.check_rate_limit("user:123", config)

        assert result.allowed is True
        assert result.current_minute == 1
        assert result.current_hour == 1
        assert result.limit_minute == 10
        assert result.limit_hour == 100

    def test_check_rate_limit_exceeded_minute(self) -> None:
        settings = make_settings(rate_limit_enabled=True)
        limiter = HybridRateLimiter(settings)
        config = RateLimitConfig(requests_per_minute=2, requests_per_hour=100)

        limiter.check_rate_limit("user:123", config)
        limiter.check_rate_limit("user:123", config)
        result = limiter.check_rate_limit("user:123", config)

        assert result.allowed is False
        assert result.current_minute == 3
        assert result.retry_after_seconds is not None
        assert 0 < result.retry_after_seconds <= 60

    def test_check_rate_limit_exceeded_hour(self) -> None:
        settings = make_settings(rate_limit_enabled=True)
        limiter = HybridRateLimiter(settings)
        config = RateLimitConfig(requests_per_minute=100, requests_per_hour=2)

        limiter.check_rate_limit("user:123", config)
        limiter.check_rate_limit("user:123", config)
        result = limiter.check_rate_limit("user:123", config)

        assert result.allowed is False
        assert result.current_hour == 3
        assert result.retry_after_seconds is not None
        assert 60 < result.retry_after_seconds <= 3600

    def test_check_rate_limit_disabled(self) -> None:
        settings = make_settings(rate_limit_enabled=False)
        limiter = HybridRateLimiter(settings)
        config = RateLimitConfig(requests_per_minute=1, requests_per_hour=1)

        result = limiter.check_rate_limit("user:123", config)

        assert result.allowed is True
        assert result.current_minute == 0
        assert result.current_hour == 0

    def test_different_identifiers_independent(self) -> None:
        settings = make_settings(rate_limit_enabled=True)
        limiter = HybridRateLimiter(settings)
        config = RateLimitConfig(requests_per_minute=2, requests_per_hour=100)

        limiter.check_rate_limit("user:1", config)
        limiter.check_rate_limit("user:1", config)
        result1 = limiter.check_rate_limit("user:1", config)

        result2 = limiter.check_rate_limit("user:2", config)

        assert result1.allowed is False
        assert result2.allowed is True
        assert result2.current_minute == 1

    def test_reset_limits(self) -> None:
        settings = make_settings(rate_limit_enabled=True)
        limiter = HybridRateLimiter(settings)
        config = RateLimitConfig(requests_per_minute=2, requests_per_hour=100)

        limiter.check_rate_limit("user:123", config)
        limiter.check_rate_limit("user:123", config)

        limiter.reset_limits("user:123")

        result = limiter.check_rate_limit("user:123", config)
        assert result.allowed is True
        assert result.current_minute == 1


class TestRateLimitingIntegration:
    """Integration tests for rate limiting on API endpoints."""

    def setup_method(self) -> None:
        reset_rate_limits_for_testing()
        app.dependency_overrides.clear()

    def teardown_method(self) -> None:
        app.dependency_overrides.clear()
        reset_rate_limits_for_testing()

    def test_chat_endpoint_rate_limit_authenticated(self) -> None:
        """Test rate limiting on /chat endpoint for authenticated user."""
        settings = make_settings(rate_limit_enabled=True, auth_enabled=True)
        user = User(id="test-user-123", email="test@example.com", hashed_password="hash", is_active=True)
        mock_chat = MagicMock()
        mock_chat.chat.return_value = _chat_result()
        install_dependency_overrides(settings, user, mock_chat, get_chat_service)

        # Make requests up to limit
        for i in range(settings.rate_limit_chat_per_minute):
            response = client.post(
                "/chat",
                json={"message": f"Test {i}", "ticker": "AAPL"},
            )
            assert response.status_code == 200, f"Request {i} failed: {response.text}"

        # Next request should be rate limited
        response = client.post(
            "/chat",
            json={"message": "Over limit", "ticker": "AAPL"},
        )
        assert response.status_code == 429
        assert "Retry-After" in response.headers

    def test_chat_endpoint_rate_limit_anonymous(self) -> None:
        """Test rate limiting on /chat endpoint for anonymous user (stricter)."""
        settings = make_settings(rate_limit_enabled=True, auth_enabled=True)
        mock_chat = MagicMock()
        mock_chat.chat.return_value = _chat_result()
        install_dependency_overrides(settings, None, mock_chat, get_chat_service)

        # Anonymous users get stricter limits (multiplier)
        anon_limit = max(1, int(settings.rate_limit_chat_per_minute * settings.rate_limit_anonymous_multiplier))

        for i in range(anon_limit):
            response = client.post(
                "/chat",
                json={"message": f"Test {i}", "ticker": "AAPL"},
            )
            assert response.status_code == 200, f"Request {i} failed: {response.text}"

        # Next request should be rate limited
        response = client.post(
            "/chat",
            json={"message": "Over limit", "ticker": "AAPL"},
        )
        assert response.status_code == 429

    def test_analyze_endpoint_rate_limit(self) -> None:
        """Test rate limiting on /analyze endpoint."""
        settings = make_settings(rate_limit_enabled=True, auth_enabled=True)
        user = User(id="test-user-123", email="test@example.com", hashed_password="hash", is_active=True)
        mock_analysis = MagicMock()
        mock_analysis.analyze_ticker.return_value = _analyze_result()
        install_dependency_overrides(settings, user, mock_analysis, get_analysis_service)

        for i in range(settings.rate_limit_analyze_per_minute):
            response = client.post(
                "/analyze",
                json={"ticker": "AAPL"},
            )
            assert response.status_code == 200, f"Request {i} failed: {response.text}"

        response = client.post(
            "/analyze",
            json={"ticker": "AAPL"},
        )
        assert response.status_code == 429


    def test_documents_endpoint_rate_limit(self) -> None:
        """Test rate limiting on /documents endpoints."""
        settings = make_settings(rate_limit_enabled=True, auth_enabled=True)
        user = User(id="test-user-123", email="test@example.com", hashed_password="hash", is_active=True)
        mock_doc = MagicMock()
        mock_doc.list_documents.return_value = {"documents": [], "total": 0}
        install_dependency_overrides(settings, user, mock_doc, get_document_service)

        for i in range(settings.rate_limit_documents_per_minute):
            response = client.get("/documents")
            assert response.status_code == 200, f"Request {i} failed: {response.text}"

        response = client.get("/documents")
        assert response.status_code == 429

    def test_search_endpoint_rate_limit(self) -> None:
        """Test rate limiting on /search endpoint."""
        settings = make_settings(rate_limit_enabled=True, auth_enabled=True)
        user = User(id="test-user-123", email="test@example.com", hashed_password="hash", is_active=True)
        mock_search = MagicMock()
        mock_search.search.return_value = _search_result()
        install_dependency_overrides(settings, user, mock_search, get_search_service)

        for i in range(settings.rate_limit_search_per_minute):
            response = client.post(
                "/search",
                json={"query": f"test {i}"},
            )
            assert response.status_code == 200, f"Request {i} failed: {response.text}"

        response = client.post(
            "/search",
            json={"query": "over limit"},
        )
        assert response.status_code == 429

    def test_rate_limit_headers_present(self) -> None:
        """Test that rate limit headers are present on 429 responses."""
        settings = make_settings(rate_limit_enabled=True, auth_enabled=True)
        user = User(id="test-user-123", email="test@example.com", hashed_password="hash", is_active=True)
        mock_chat = MagicMock()
        mock_chat.chat.return_value = _chat_result()
        install_dependency_overrides(settings, user, mock_chat, get_chat_service)

        # Exhaust the per-minute limit
        for i in range(settings.rate_limit_chat_per_minute):
            response = client.post(
                "/chat",
                json={"message": f"Test {i}", "ticker": "AAPL"},
            )
            assert response.status_code == 200

        response = client.post(
            "/chat",
            json={"message": "Over limit", "ticker": "AAPL"},
        )

        assert response.status_code == 429
        assert "Retry-After" in response.headers
        assert "X-RateLimit-Limit-Minute" in response.headers
        assert "X-RateLimit-Remaining-Minute" in response.headers
        assert "X-RateLimit-Limit-Hour" in response.headers
        assert "X-RateLimit-Remaining-Hour" in response.headers

    def test_rate_limit_reset_between_windows(self) -> None:
        """Test that the limiter tracks time-windowed counters correctly."""
        settings = make_settings(rate_limit_enabled=True)
        limiter = HybridRateLimiter(settings)
        config = RateLimitConfig(requests_per_minute=2, requests_per_hour=100)

        limiter.check_rate_limit("user:123", config)
        limiter.check_rate_limit("user:123", config)
        result = limiter.check_rate_limit("user:123", config)
        assert result.allowed is False
        assert result.retry_after_seconds is not None

        # Counters are keyed by the concrete minute/hour window
        minute_key = f"ratelimit:user:123:minute:{int(time.time() // 60)}"
        hour_key = f"ratelimit:user:123:hour:{int(time.time() // 3600)}"
        backend = limiter._get_backend()
        assert backend.get(minute_key) == 3
        assert backend.get(hour_key) == 3

        # Resetting the identifier clears both counters
        limiter.reset_limits("user:123")
        assert backend.get(minute_key) == 0
        assert backend.get(hour_key) == 0


class TestRateLimitConcurrency:
    """Tests for concurrent request handling."""

    def setup_method(self) -> None:
        reset_rate_limits_for_testing()

    def teardown_method(self) -> None:
        reset_rate_limits_for_testing()

    def test_concurrent_requests_local_backend(self) -> None:
        """Test that concurrent requests are handled correctly with local backend."""
        import threading

        settings = make_settings(rate_limit_enabled=True)
        limiter = HybridRateLimiter(settings)
        config = RateLimitConfig(requests_per_minute=100, requests_per_hour=1000)

        results = []
        num_threads = 20
        requests_per_thread = 5

        def make_requests() -> None:
            for _ in range(requests_per_thread):
                result = limiter.check_rate_limit("user:concurrent", config)
                results.append(result.allowed)

        threads = []
        for _ in range(num_threads):
            t = threading.Thread(target=make_requests)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # All requests should be allowed (well under limit)
        allowed_count = sum(1 for r in results if r)
        assert allowed_count == num_threads * requests_per_thread

    def test_concurrent_requests_exceed_limit(self) -> None:
        """Test that concurrent requests correctly hit the limit."""
        import threading

        settings = make_settings(rate_limit_enabled=True)
        limiter = HybridRateLimiter(settings)
        config = RateLimitConfig(requests_per_minute=10, requests_per_hour=100)

        results = []
        num_threads = 5
        requests_per_thread = 5  # Total 25, limit is 10

        def make_requests() -> None:
            for _ in range(requests_per_thread):
                result = limiter.check_rate_limit("user:concurrent2", config)
                results.append(result.allowed)

        threads = []
        for _ in range(num_threads):
            t = threading.Thread(target=make_requests)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Exactly 10 should be allowed, rest denied
        allowed_count = sum(1 for r in results if r)
        denied_count = sum(1 for r in results if not r)
        assert allowed_count == 10
        assert denied_count == 15


class TestRateLimitingDisabled:
    """Tests when rate limiting is disabled."""

    def setup_method(self) -> None:
        reset_rate_limits_for_testing()
        app.dependency_overrides.clear()

    def teardown_method(self) -> None:
        app.dependency_overrides.clear()
        reset_rate_limits_for_testing()

    def test_rate_limiting_disabled_allows_all(self) -> None:
        """Test that disabling rate limiting allows unlimited requests."""
        settings = make_settings(rate_limit_enabled=False, auth_enabled=True)
        user = User(id="test-user-123", email="test@example.com", hashed_password="hash", is_active=True)
        mock_chat = MagicMock()
        mock_chat.chat.return_value = _chat_result()
        install_dependency_overrides(settings, user, mock_chat, get_chat_service)

        # Make many requests - all should succeed
        for i in range(100):
            response = client.post(
                "/chat",
                json={"message": f"Test {i}", "ticker": "AAPL"},
            )
            assert response.status_code == 200, f"Request {i} failed: {response.text}"


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures and utilities
# ──────────────────────────────────────────────────────────────────────────────

import threading


@pytest.fixture(autouse=True)
def reset_rate_limiter_fixture() -> None:
    """Auto-reset rate limiter before each test."""
    reset_rate_limits_for_testing()
    yield
    reset_rate_limits_for_testing()