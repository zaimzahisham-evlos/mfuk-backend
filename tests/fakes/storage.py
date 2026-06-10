"""in-memory S3 fake storage client for testing"""
from __future__ import annotations

from botocore.exceptions import ClientError

class FakeStorageClient:
    f"""
    Mimics the subset of S3StorageClient the production code uses.
    Keys are (bucket, object_key) -> dict(size, content_type).
    """

    def __init__(self) -> None:
        self.objects: dict[tuple[str, str], dict] = {}

    def presign_put(self, bucket: str, key: str, content_type: str) -> str:
        return f"http://fake-storage/upload/{bucket}/{key}?content_type={content_type}"

    def presign_get(self, bucket: str, key: str) -> str:
        return f"http://fake-storage/download/{bucket}/{key}"

    def head(self, bucket: str, key: str) -> dict:
        obj = self.objects.get((bucket, key))
        if not obj:
            raise ClientError(
                {"Error": {"Code": "404", "Message": "Not Found"}},
                "HeadObject"
            )
        
        return {
            "ContentLength": obj["size"],
            "ContentType": obj["content_type"],
        }

    def delete(self, bucket: str, key: str) -> None:
        self.objects.pop((bucket, key), None)

    def ensure_bucket(self, bucket: str) -> None:
        pass

    def ping(self) -> bool:
        return True

    def put_object(self, bucket: str, key: str, data: bytes, content_type: str) -> None:
        """Simulates frontend PUT after init"""
        self.objects[(bucket, key)] = {
            "size": len(data),
            "content_type": content_type,
        }