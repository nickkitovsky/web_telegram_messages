from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_ignore_empty=True,
    )

    app_secret_key: str = "development-only-replace-this"
    cookie_secure: bool = False
    database_url: str = (
        "postgresql+asyncpg://saved_messages:saved_messages@localhost:5432/saved_messages"
    )
    redis_url: str = "redis://localhost:6379/0"
    telegram_api_id: int | None = None
    telegram_api_hash: str | None = None
    telegram_proxy_url: str | None = None
    telegram_session_encryption_key: str | None = None
    media_storage_path: str = "data/media"
    llm_model_path: str = "models/Qwen3-0.6B-Q4_K_M.gguf"
    llm_confidence_threshold: float = 0.7


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
