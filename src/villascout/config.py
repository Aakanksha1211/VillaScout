from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    google_api_key: str = Field(default="", alias="GOOGLE_API_KEY")
    database_url: str = Field(default="sqlite+aiosqlite:///./villascout.db", alias="DATABASE_URL")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    cache_directory: Path = Field(default=Path("cache"), alias="CACHE_DIRECTORY")
    cache_ttl_seconds: int = Field(default=86_400, alias="CACHE_TTL_SECONDS")
    request_timeout_seconds: float = 20.0
    max_retries: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
