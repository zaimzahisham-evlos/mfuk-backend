# app/storage/client.py
from dataclasses import dataclass
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
import logging

@dataclass
class StorageSettings:
    endpoint_internal: str
    endpoint_public: str
    access_key: str
    secret_key: str
    region: str
    use_ssl: bool
    upload_expiry: int
    download_expiry: int

class S3StorageClient:
    def __init__(self, s: StorageSettings):
        self._internal = boto3.client(
            "s3",
            endpoint_url=s.endpoint_internal,
            aws_access_key_id=s.access_key,
            aws_secret_access_key=s.secret_key,
            region_name=s.region,
            use_ssl=s.use_ssl,
            config=Config(signature_version="s3v4"),
        )
        self._public = boto3.client(
            "s3",
            endpoint_url=s.endpoint_public,
            aws_access_key_id=s.access_key,
            aws_secret_access_key=s.secret_key,
            region_name=s.region,
            use_ssl=s.use_ssl,
            config=Config(signature_version="s3v4"),
        )
        self.s = s

    def presign_put(self, bucket: str, key: str, content_type: str) -> str:
        return self._public.generate_presigned_url(
            "put_object",
            Params={"Bucket": bucket, "Key": key, "ContentType": content_type},
            ExpiresIn=self.s.upload_expiry,
        )

    def presign_get(self, bucket: str, key: str) -> str:
        return self._public.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=self.s.download_expiry,
        )

    def head(self, bucket: str, key: str):
        return self._internal.head_object(Bucket=bucket, Key=key)

    def delete(self, bucket: str, key: str):
        self._internal.delete_object(Bucket=bucket, Key=key)

    def ensure_bucket(self, bucket: str) -> None:
        try:
            self._internal.head_bucket(Bucket=bucket)
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            if code not in ("404", "NoSuchBucket", "NotFound"):
                raise
            self._internal.create_bucket(Bucket=bucket)
            logging.info(f"Created bucket: {bucket}")

    def ping(self) -> bool:
        try:
            self._internal.list_buckets()
            return True
        except Exception:
            logging.exception("Storage ping failed")
            return False