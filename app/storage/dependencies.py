from functools import lru_cache

from app.core.config import settings
from app.storage.client import S3StorageClient, StorageSettings


@lru_cache
def get_storage_client() -> S3StorageClient:
    return S3StorageClient(
        StorageSettings(
            endpoint_internal=settings.S3_ENDPOINT_INTERNAL,
            endpoint_public=settings.S3_ENDPOINT_PUBLIC,
            access_key=settings.S3_ACCESS_KEY,
            secret_key=settings.S3_SECRET_KEY,
            region=settings.S3_REGION,
            use_ssl=settings.S3_USE_SSL,
            upload_expiry=settings.S3_PRESIGN_UPLOAD_EXPIRE_SECONDS,
            download_expiry=settings.S3_PRESIGN_DOWNLOAD_EXPIRE_SECONDS,
        )
    )


def bootstrap_storage() -> None:
    client = get_storage_client()
    if settings.S3_AUTO_CREATE_BUCKETS:
        client.ensure_bucket(settings.S3_BUCKET_REPOSITORY_IMAGES)