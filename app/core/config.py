from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List
from pydantic import SecretStr, ConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    PROJECT_NAME: str = "FastAPI Starter"
    DEBUG: bool = False

    DATABASE_URL: str = ""
    POSTGRES_DB: str = ""
    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str = ""
    TEST_DATABASE_URL: str = ""
    SUPERADMIN_PASSWORD: str = ""

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    SECRET_KEY: SecretStr = SecretStr("temporary_secret_key_for_initialization")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 2
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 5

    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
    CORS_ORIGINS: List[str] = ["*"]

settings = Settings()
