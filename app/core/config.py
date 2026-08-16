from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_", extra="ignore")

    database_url: str
    secret_key: str
    access_ttl_minutes: int = 15
    openai_api_key: str | None = None
    environment: str = "dev"

@lru_cache
def get_settings() -> Settings:
    return Settings()      # cached singleton
