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

    OBJECT_STORAGE_PROVIDER: str = "seaweedfs"
    S3_ENDPOINT_INTERNAL: str = "http://seaweed-s3:8333"
    S3_ENDPOINT_PUBLIC: str = "http://localhost:8333"
    S3_ACCESS_KEY: str = "seaweed_access_key"
    S3_SECRET_KEY: str = "seaweed_secret_key"
    S3_BUCKET: str = "mfuk-backend-bucket"
    S3_BUCKET_REPOSITORY_IMAGES: str = "repository-images"
    S3_REGION: str = "us-east-1"
    S3_USE_SSL: bool = False
    S3_PRESIGN_UPLOAD_EXPIRE_SECONDS: int = 900 # 15 minutes
    S3_PRESIGN_DOWNLOAD_EXPIRE_SECONDS: int = 3600 # 1 hour
    S3_AUTO_CREATE_BUCKETS: bool = True
    MAX_REPOSITORY_IMAGE_BYTES: int = 104857600 # 100MB
    MAX_REPOSITORY_IMAGES_PER_RECIPE_VERSION: int = 100
    ALLOWED_IMAGE_CONTENT_TYPES: List[str] = ["image/jpeg", "image/png", "image/webp", "image/tiff"]

settings = Settings()
