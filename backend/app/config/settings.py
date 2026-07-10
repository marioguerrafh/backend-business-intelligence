from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "BI Platform API"
    app_env: str = "development"
    app_debug: bool = False
    api_v1_prefix: str = "/v1"

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/bi"

    jwt_secret_key: str = "dev-only-change-me"
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "bi-platform-api"
    jwt_audience: str = "bi-platform-clients"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_minutes: int = 7 * 24 * 60

    auth_storage_mode: str = "memory"
    auth_seed_demo_users: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
