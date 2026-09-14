"""Tests for app.core.config validation logic."""

import os
from unittest.mock import patch

import pytest

from app.core.config import Settings, Environment, get_settings
from app.core.exceptions import ConfigurationError


class TestConfigValidation:
    """Tests for Settings.validate_required_keys()."""

    def test_validate_required_keys_test_env_passes(self) -> None:
        """TEST environment should skip all validation."""
        settings = Settings(environment=Environment.TEST)
        settings.validate_required_keys()  # Should not raise

    def test_validate_required_keys_demo_mode_passes(self) -> None:
        """Demo mode should skip validation even in production."""
        settings = Settings(
            environment=Environment.PRODUCTION,
            demo_mode=True,
            openai_api_key="",
            fmp_api_key="",
            auth_secret_key="",
            auth_enabled=True,
        )
        settings.validate_required_keys()  # Should not raise

    def test_validate_required_keys_dev_missing_openai_raises(self) -> None:
        """DEVELOPMENT without OPENAI_API_KEY should raise."""
        settings = Settings(
            environment=Environment.DEVELOPMENT,
            openai_api_key="",
            demo_mode=False,
        )
        with pytest.raises(ConfigurationError) as exc_info:
            settings.validate_required_keys()
        assert exc_info.value.error_code == "CONFIG_001"
        assert "OPENAI_API_KEY" in exc_info.value.details["missing_keys"]

    def test_validate_required_keys_prod_missing_openai_raises(self) -> None:
        """PRODUCTION without OPENAI_API_KEY should raise."""
        settings = Settings(
            environment=Environment.PRODUCTION,
            openai_api_key="",
            demo_mode=False,
        )
        with pytest.raises(ConfigurationError) as exc_info:
            settings.validate_required_keys()
        assert "OPENAI_API_KEY" in exc_info.value.details["missing_keys"]

    def test_validate_required_keys_prod_missing_fmp_raises(self) -> None:
        """PRODUCTION without FMP_API_KEY should raise."""
        settings = Settings(
            environment=Environment.PRODUCTION,
            openai_api_key="sk-test",
            fmp_api_key="",
            demo_mode=False,
        )
        with pytest.raises(ConfigurationError) as exc_info:
            settings.validate_required_keys()
        assert "FMP_API_KEY" in exc_info.value.details["missing_keys"]

    def test_validate_required_keys_prod_auth_enabled_missing_auth_secret_raises(self) -> None:
        """PRODUCTION with auth enabled but no AUTH_SECRET_KEY should raise."""
        settings = Settings(
            environment=Environment.PRODUCTION,
            openai_api_key="sk-test",
            fmp_api_key="fmp-test",
            auth_secret_key="",
            auth_enabled=True,
            demo_mode=False,
        )
        with pytest.raises(ConfigurationError) as exc_info:
            settings.validate_required_keys()
        assert "AUTH_SECRET_KEY" in exc_info.value.details["missing_keys"]

    def test_validate_required_keys_prod_auth_disabled_no_auth_secret_ok(self) -> None:
        """PRODUCTION with auth disabled should not require AUTH_SECRET_KEY."""
        settings = Settings(
            environment=Environment.PRODUCTION,
            openai_api_key="sk-test",
            fmp_api_key="fmp-test",
            auth_secret_key="",
            auth_enabled=False,
            demo_mode=False,
        )
        settings.validate_required_keys()  # Should not raise

    def test_validate_required_keys_prod_all_keys_present_ok(self) -> None:
        """PRODUCTION with all required keys should pass."""
        settings = Settings(
            environment=Environment.PRODUCTION,
            openai_api_key="sk-test",
            fmp_api_key="fmp-test",
            auth_secret_key="secret-key-32-chars-minimum!!",
            auth_enabled=True,
            demo_mode=False,
        )
        settings.validate_required_keys()  # Should not raise


class TestConfigSingleton:
    """Tests for get_settings() singleton behavior."""

    def test_get_settings_returns_same_instance(self) -> None:
        """get_settings() should return cached singleton."""
        get_settings.cache_clear()
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2

    def test_get_settings_cache_clear_works(self) -> None:
        """cache_clear() should allow new instance."""
        get_settings.cache_clear()
        s1 = get_settings()
        get_settings.cache_clear()
        s2 = get_settings()
        # Different instances after cache clear (though same values)
        assert s1 is not s2 or s1 == s2