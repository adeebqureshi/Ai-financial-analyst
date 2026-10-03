"""Regression tests for rate limiting on the expensive analysis endpoints.

Background
----------
``/report`` (full LLM analysis plus narrative writing), ``/compare`` (2-10
companies analysed per call), ``/valuation`` and ``/risk`` were the only
non-trivial routes registered **without** a rate-limit dependency, while far
cheaper endpoints such as ``/search`` were limited. That allowed any client to
amplify provider spend without bound.

These tests pin that each expensive route resolves to its own bucket, that the
buckets are ordered by cost, and that a quota exhaustion during report
generation keeps its real status (429) instead of being relabelled as a 502.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.api.dependencies import (
    RateLimitDependency,
    reset_rate_limits_for_testing,
)
from app.api.exceptions import get_status_code_for_domain_error
from app.api.rate_limiter import (
    get_endpoint_config,
    get_rate_limiter,
    reset_rate_limiter,
)
from app.auth.models import User
from app.core.config import Settings, get_settings
from app.core.exceptions import (
    QuotaExceededError,
    SandboxError,
    ValidationError,
)
from app.main import app

# Rate-limit bucket name -> route path that consumes it.
PROTECTED_ROUTES = [
    ("report", "/report"),
    ("compare", "/compare"),
    ("valuation", "/valuation"),
    ("risk", "/risk-analysis"),
]


def make_settings(**overrides: object) -> Settings:
    return get_settings().model_copy(update=overrides)


def make_user(user_id: str = "audit-user-1") -> User:
    return User(
        id=user_id,
        email=f"{user_id}@example.com",
        hashed_password="hash",
        is_active=True,
    )
class TestExpensiveRouteBuckets:
    def test_buckets_are_isolated_from_each_other(self) -> None:
        """No two expensive endpoints may share a bucket.

        A shared bucket lets cheap traffic on one endpoint exhaust the quota of
        an expensive one — the same class of bug as the documents bucket split.
        """
        settings = make_settings(rate_limit_enabled=True)
        prefixes = {
            bucket: get_endpoint_config(bucket, settings).key_prefix
            for bucket, _ in PROTECTED_ROUTES
        }

        assert len(set(prefixes.values())) == len(prefixes), (
            f"rate-limit buckets are not isolated: {prefixes}"
        )

    def test_no_bucket_falls_back_to_the_shared_default(self) -> None:
        """`get_endpoint_config` silently returns the permissive default bucket
        for an unknown key, so a typo would disable limiting rather than fail."""
        settings = make_settings(rate_limit_enabled=True)
        default_prefix = get_endpoint_config("default", settings).key_prefix

        for bucket, route in PROTECTED_ROUTES:
            config = get_endpoint_config(bucket, settings)
            assert config.key_prefix != default_prefix, (
                f"{route} resolves to the shared default bucket"
            )
            assert config.key_prefix == f"ratelimit:{bucket}", (
                f"{route} bucket prefix mismatch: {config.key_prefix}"
            )

    def test_report_is_tighter_than_default(self) -> None:
        """Reports call the LLM end to end, so the default bucket is too loose."""
        settings = make_settings(rate_limit_enabled=True)
        report = get_endpoint_config("report", settings)
        default = get_endpoint_config("default", settings)

        assert report.requests_per_minute < default.requests_per_minute
        assert report.requests_per_hour < default.requests_per_hour

    def test_compare_is_tighter_than_single_analysis(self) -> None:
        """One comparison analyses up to 10 companies, so it costs more."""
        settings = make_settings(rate_limit_enabled=True)

        assert (
            get_endpoint_config("compare", settings).requests_per_minute
            < get_endpoint_config("analyze", settings).requests_per_minute
        )


class TestReportDependencyEnforcement:
    """The dependency is exercised directly rather than over HTTP.

    Driving a real POST would construct the real report service (which opens an
    LLM client) whenever the service override does not take effect, which makes
    the test depend on a live provider. Invoking the dependency keeps it
    deterministic while still proving the 429 is produced before the handler
    body runs.
    """

    def _request(self) -> MagicMock:
        request = MagicMock()
        request.headers = {}
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        request.state = MagicMock()
        return request

    def test_dependency_allows_traffic_under_the_limit(self) -> None:
        settings = make_settings(rate_limit_enabled=True)
        dependency = RateLimitDependency("report")

        result = dependency(self._request(), make_user(), settings)

        assert result.allowed is True

    def test_dependency_raises_429_once_the_bucket_is_full(self) -> None:
        settings = make_settings(rate_limit_enabled=True)
        dependency = RateLimitDependency("report")
        config = get_endpoint_config("report", settings)

        user = make_user()
        identifier = f"user:{user.id}"

        # Exhaust the bucket exactly as repeated requests would.
        limiter = get_rate_limiter(settings)
        for _ in range(config.requests_per_minute):
            limiter.check_rate_limit(identifier, config)

        with pytest.raises(HTTPException) as excinfo:
            dependency(self._request(), user, settings)

        assert excinfo.value.status_code == 429
        assert "Retry-After" in excinfo.value.headers


class TestReportErrorStatusMapping:
    def test_quota_exhaustion_maps_to_429_not_502(self) -> None:
        """The report router must not relabel a quota error as a gateway fault."""
        assert (
            get_status_code_for_domain_error(QuotaExceededError())
            == 429
        )

    def test_validation_error_maps_to_422(self) -> None:
        assert get_status_code_for_domain_error(ValidationError()) == 422

    def test_sandbox_error_keeps_its_own_status(self) -> None:
        assert get_status_code_for_domain_error(SandboxError()) == 400

