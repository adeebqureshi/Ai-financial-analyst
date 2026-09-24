import os
from unittest.mock import patch
import pytest
from app.core.config import Settings, Environment, get_settings
from app.core.exceptions import ConfigurationError
class TestConfigValidation:
    def test_validate_required_keys_test_env_passes(self) -> None:
        settings = Settings(environment=Environment.TEST)
        settings.validate_required_keys()
    def test_validate_required_keys_demo_mode_passes(self) -> None:
        settings = Settings(
            environment=Environment.PRODUCTION,
            demo_mode=True,
            openai_api_key="",
            fmp_api_key="",
            auth_secret_key="",
            auth_enabled=True,
        )
        settings.validate_required_keys()
    def test_validate_required_keys_dev_missing_openai_raises(self) -> None:
        settings = Settings(
            environment=Environment.DEVELOPMENT,
            llm_provider="openai",
            openai_api_key="",
            freellmapi_base_url="",
            freellmapi_api_key="",
            demo_mode=False,
        )
        with pytest.raises(ConfigurationError) as exc_info:
            settings.validate_required_keys()
        assert exc_info.value.error_code == "CONFIG_001"
        assert "OPENAI_API_KEY" in exc_info.value.details["missing_keys"]
    def test_validate_required_keys_prod_missing_openai_raises(self) -> None:
        settings = Settings(
            environment=Environment.PRODUCTION,
            llm_provider="openai",
            openai_api_key="",
            freellmapi_base_url="",
            freellmapi_api_key="",
            demo_mode=False,
        )
        with pytest.raises(ConfigurationError) as exc_info:
            settings.validate_required_keys()
        assert "OPENAI_API_KEY" in exc_info.value.details["missing_keys"]
    def test_validate_required_keys_prod_missing_fmp_raises(self) -> None:
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
        settings = Settings(
            environment=Environment.PRODUCTION,
            openai_api_key="sk-test",
            fmp_api_key="fmp-test",
            auth_secret_key="",
            auth_enabled=False,
            demo_mode=False,
        )
        settings.validate_required_keys()
    def test_validate_required_keys_prod_all_keys_present_ok(self) -> None:
        settings = Settings(
            environment=Environment.PRODUCTION,
            openai_api_key="sk-test",
            fmp_api_key="fmp-test",
            auth_secret_key="secret-key-32-chars-minimum!!",
            auth_enabled=True,
            demo_mode=False,
        )
        settings.validate_required_keys()
class TestModuleLevelSettings:
    def test_module_level_settings_object_is_exposed(self) -> None:
        from app.core.config import settings as module_settings
        from app.core.config import get_settings
        assert isinstance(module_settings, Settings)
        assert module_settings.edgar_identity == get_settings().edgar_identity
    def test_edgar_client_can_import_module_settings(self) -> None:
        from app.ingestion.clients import edgar_client
        assert isinstance(edgar_client.settings, Settings)
class TestFreeLLMAPICompatibility:
    def test_freellmapi_satisfies_llm_requirement_without_openai_key(self) -> None:
        settings = Settings(
            environment=Environment.DEVELOPMENT,
            llm_provider="openai",
            openai_api_key="",
            freellmapi_base_url="http://localhost:3001/v1",
            freellmapi_api_key="test-freellmapi-key",
            demo_mode=False,
        )
        assert settings.uses_freellmapi is True
        assert settings.freellmapi_api_key_str == "test-freellmapi-key"
        assert settings.openai_api_key_str == ""
        settings.validate_required_keys()
    def test_freellmapi_satisfies_production_validation_with_fmp_key(self) -> None:
        settings = Settings(
            environment=Environment.PRODUCTION,
            llm_provider="openai",
            openai_api_key="",
            freellmapi_base_url="http://localhost:3001/v1",
            freellmapi_api_key="test-freellmapi-key",
            fmp_api_key="fmp-test",
            auth_enabled=False,
            demo_mode=False,
        )
        settings.validate_required_keys()
    def test_freellmapi_requires_base_url_and_key(self) -> None:
        settings = Settings(
            environment=Environment.DEVELOPMENT,
            llm_provider="openai",
            openai_api_key="",
            freellmapi_base_url="",
            freellmapi_api_key="test-freellmapi-key",
            demo_mode=False,
        )
        assert settings.uses_freellmapi is False
        with pytest.raises(ConfigurationError) as exc_info:
            settings.validate_required_keys()
        assert "OPENAI_API_KEY" in exc_info.value.details["missing_keys"]
class TestConfigSingleton:
    def test_get_settings_returns_same_instance(self) -> None:
        get_settings.cache_clear()
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2
    def test_get_settings_cache_clear_works(self) -> None:
        get_settings.cache_clear()
        s1 = get_settings()
        get_settings.cache_clear()
        s2 = get_settings()
        assert s1 is not s2 or s1 == s2