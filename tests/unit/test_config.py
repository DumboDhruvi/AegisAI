"""Unit tests for Settings configuration in aegis.core.config."""

from __future__ import annotations

import os
from unittest.mock import patch

from aegis.core.config import Settings


def test_default_settings() -> None:
    """Ensure default settings initialize with correct types and fallback values."""
    settings = Settings()
    assert settings.environment == "development"
    assert settings.log_level == "INFO"
    assert settings.host == "0.0.0.0"
    assert settings.port == 8000
    assert settings.default_evaluation_temperature == 0.0
    assert settings.embedding_dimensions == 1536
    assert settings.max_evaluation_retries == 3
    assert settings.evaluation_timeout_seconds == 30


def test_settings_from_environment_variables() -> None:
    """Ensure environment variable aliases override default settings properly."""
    env_overrides = {
        "AEGIS_ENV": "production",
        "AEGIS_LOG_LEVEL": "DEBUG",
        "AEGIS_PORT": "9000",
        "DEFAULT_EVALUATION_TEMPERATURE": "0.7",
        "OPENAI_API_KEY": "test-key-mock",
        "EMBEDDING_DIMENSIONS": "768",
    }
    with patch.dict(os.environ, env_overrides, clear=False):
        settings = Settings()
        assert settings.environment == "production"
        assert settings.log_level == "DEBUG"
        assert settings.port == 9000
        assert settings.default_evaluation_temperature == 0.7
        assert settings.openai_api_key == "test-key-mock"
        assert settings.embedding_dimensions == 768
