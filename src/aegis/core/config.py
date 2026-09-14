"""Configuration management for AegisAI using pydantic-settings."""

from __future__ import annotations

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    environment: Literal["development", "testing", "staging", "production"] = Field(
        default="development", alias="AEGIS_ENV"
    )
    log_level: str = Field(default="INFO", alias="AEGIS_LOG_LEVEL")
    host: str = Field(default="0.0.0.0", alias="AEGIS_HOST")
    port: int = Field(default=8000, alias="AEGIS_PORT")

    # Database & Vector Store
    database_url: str = Field(
        default="postgresql://aegis_user:aegis_password@localhost:5432/aegis_db",
        alias="DATABASE_URL",
    )

    # LLM Providers
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")

    # Embeddings
    embedding_provider: str = Field(default="openai", alias="EMBEDDING_PROVIDER")
    embedding_model: str = Field(default="text-embedding-3-small", alias="EMBEDDING_MODEL")
    embedding_dimensions: int = Field(default=1536, alias="EMBEDDING_DIMENSIONS")

    # Evaluation Controls
    default_evaluation_temperature: float = Field(
        default=0.0, alias="DEFAULT_EVALUATION_TEMPERATURE"
    )
    max_evaluation_retries: int = Field(default=3, alias="MAX_EVALUATION_RETRIES")
    evaluation_timeout_seconds: int = Field(default=30, alias="EVALUATION_TIMEOUT_SECONDS")


settings = Settings()
