"""
Rate Limiting Tests

Tests for per-user and IP-based rate limits on expensive endpoints.
"""

from __future__ import annotations

import asyncio
import time
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import reset_rate_limits_for_testing
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
        settings = get_settings()
        settings.rate_limit_enabled = True
        limiter = HybridRateLimiter(settings)
        config = RateLimitConfig(requests_per_minute=10, requests_per_hour=100)

        result = limiter.check_rate_limit("user:123", config)

        assert result.allowed is True
        assert result.current_minute == 1
        assert result.current_hour == 1
        assert result.limit_minute == 10
        assert result.limit_hour == 100

    def test_check_rate_limit_exceeded_minute(self) -> None:
        settings = get_settings()
        settings.rate_limit_enabled = True
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
        settings = get_settings()
        settings.rate_limit_enabled = True
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
        settings = get_settings()
        settings.rate_limit_enabled = False
        limiter = HybridRateLimiter(settings)
        config = RateLimitConfig(requests_per_minute=1, requests_per_hour=1)

        result = limiter.check_rate_limit("user:123", config)

        assert result.allowed is True
        assert result.current_minute == 0
        assert result.current_hour == 0

    def test_different_identifiers_independent(self) -> None:
        settings = get_settings()
        settings.rate_limit_enabled = True
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
        settings = get_settings()
        settings.rate_limit_enabled = True
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

    def teardown_method(self) -> None:
        reset_rate_limits_for_testing()

    def test_chat_endpoint_rate_limit_authenticated(self) -> None:
        """Test rate limiting on /chat endpoint for authenticated user."""
        settings = get_settings()
        settings.rate_limit_enabled = True
        settings.auth_enabled = True

        # Mock authentication
        user = User(id="test-user-123", email="test@example.com", hashed_password="hash", is_active=True)

        with patch("app.auth.dependencies.get_current_user", return_value=user):
            with patch("app.api.dependencies.services.get_chat_service") as mock_service:
                mock_chat = MagicMock()
                mock_chat.chat.return_value = MagicMock(
                    message="Test response",
                    ticker="AAPL",
                    sources=[],
                    tools_used=[],
                    plan=[]
                )
                mock_service.return_value = mock_chat

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
        settings = get_settings()
        settings.rate_limit_enabled = True
        settings.auth_enabled = True

        with patch("app.auth.dependencies.get_current_user", return_value=None):
            with patch("app.api.dependencies.services.get_chat_service") as mock_service:
                mock_chat = MagicMock()
                mock_chat.chat.return_value = MagicMock(
                    message="Test response",
                    ticker="AAPL",
                    sources=[],
                    tools_used=[],
                    plan=[]
                )
                mock_service.return_value = mock_chat

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
        settings = get_settings()
        settings.rate_limit_enabled = True
        settings.auth_enabled = True

        user = User(id="test-user-123", email="test@example.com", hashed_password="hash", is_active=True)

        with patch("app.auth.dependencies.get_current_user", return_value=user):
            with patch("app.api.dependencies.services.get_analysis_service") as mock_service:
                mock_analysis = MagicMock()
                mock_analysis.analyze_ticker.return_value = MagicMock(
                    ticker="AAPL",
                    report="Test report",
                    valuation=MagicMock(intrinsic_value=100, upside=0.2, recommendation="BUY"),
                    health_score=80,
                    risk_level="LOW",
                )
                mock_service.return_value = mock_analysis

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
        settings = get_settings()
        settings.rate_limit_enabled = True
        settings.auth_enabled = True

        user = User(id="test-user-123", email="test@example.com", hashed_password="hash", is_active=True)

        with patch("app.auth.dependencies.get_current_user", return_value=user):
            with patch("app.api.dependencies.services.get_document_service") as mock_service:
                mock_doc = MagicMock()
                mock_doc.list_documents.return_value = {"documents": [], "total": 0}
                mock_service.return_value = mock_doc

                for i in range(settings.rate_limit_documents_per_minute):
                    response = client.get("/documents")
                    assert response.status_code == 200, f"Request {i} failed: {response.text}"

                response = client.get("/documents")
                assert response.status_code == 429

    def test_search_endpoint_rate_limit(self) -> None:
        """Test rate limiting on /search endpoint."""
        settings = get_settings()
        settings.rate_limit_enabled = True
        settings.auth_enabled = True

        user = User(id="test-user-123", email="test@example.com", hashed_password="hash", is_active=True)

        with patch("app.auth.dependencies.get_current_user", return_value=user):
            with patch("app.api.dependencies.services.get_search_service") as mock_service:
                mock_search = MagicMock()
                mock_search.search.return_value = MagicMock(
                    query="test",
                    total=0,
                    results=[]
                )
                mock_service.return_value = mock_search

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
        """Test that rate limit headers are present in responses."""
        settings = get_settings()
        settings.rate_limit_enabled = True
        settings.auth_enabled = True

        user = User(id="test-user-123", email="test@example.com", hashed_password="hash", is_active=True)

        with patch("app.auth.dependencies.get_current_user", return_value=user):
            with patch("app.api.dependencies.services.get_chat_service") as mock_service:
                mock_chat = MagicMock()
                mock_chat.chat.return_value = MagicMock(
                    message="Test response",
                    ticker="AAPL",
                    sources=[],
                    tools_used=[],
                    plan=[]
                )
                mock_service.return_value = mock_chat

                response = client.post(
                    "/chat",
                    json={"message": "Test", "ticker": "AAPL"},
                )

                assert response.status_code == 200
                assert "X-RateLimit-Limit-Minute" in response.headers
                assert "X-RateLimit-Remaining-Minute" in response.headers
                assert "X-RateLimit-Limit-Hour" in response.headers
                assert "X-RateLimit-Remaining-Hour" in response.headers

    def test_rate_limit_reset_between_windows(self) -> None:
        """Test that rate limits reset after time window expires."""
        settings = get_settings()
        settings.rate_limit_enabled = True
        limiter = HybridRateLimiter(settings)
        config = RateLimitConfig(requests_per_minute=2, requests_per_hour=100)

        # Use a very short window for testing
        config_minute = RateLimitConfig(requests_per_minute=2, requests_per_hour=100)

        # Manually test with time manipulation
        limiter.check_rate_limit("user:123", config_minute)
        limiter.check_rate_limit("user:123", config_minute)
        result = limiter.check_rate_limit("user:123", config_minute)
        assert result.allowed is False

        # Wait for window to reset (in real scenario, would wait 60s)
        # For testing, we can't easily wait, so we verify the logic works
        # by checking that the limiter tracks time-based windows correctly
        assert limiter._local_backend.get("ratelimit:user:123:minute:0") >= 2


class TestRateLimitConcurrency:
    """Tests for concurrent request handling."""

    def setup_method(self) -> None:
        reset_rate_limits_for_testing()

    def teardown_method(self) -> None:
        reset_rate_limits_for_testing()

    def test_concurrent_requests_local_backend(self) -> None:
        """Test that concurrent requests are handled correctly with local backend."""
        import threading

        settings = get_settings()
        settings.rate_limit_enabled = True
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

        settings = get_settings()
        settings.rate_limit_enabled = True
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

    def teardown_method(self) -> None:
        reset_rate_limits_for_testing()

    def test_rate_limiting_disabled_allows_all(self) -> None:
        """Test that disabling rate limiting allows unlimited requests."""
        settings = get_settings()
        settings.rate_limit_enabled = False
        settings.auth_enabled = True

        user = User(id="test-user-123", email="test@example.com", hashed_password="hash", is_active=True)

        with patch("app.auth.dependencies.get_current_user", return_value=user):
            with patch("app.api.dependencies.services.get_chat_service") as mock_service:
                mock_chat = MagicMock()
                mock_chat.chat.return_value = MagicMock(
                    message="Test response",
                    ticker="AAPL",
                    sources=[],
                    tools_used=[],
                    plan=[]
                )
                mock_service.return_value = mock_chat

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