from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_")

    database_url: str
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str
    access_ttl_minutes: int = 15
    openai_api_key: str | None = None
    environment: str = "dev"

@lru_cache
def get_settings() -> Settings:
    return Settings()      # cached singleton
