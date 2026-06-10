"""
Shared steps for the repository-image upload workflow in tests.
"""

from httpx import AsyncClient, Response
from tests.fakes.storage import FakeStorageClient

DRAFT_RECIPE_VERSION_CODE = "TEST_RECIPE_VERSION_001"
RELEASED_CANDIDATE_VERSION_CODE = "TEST_RECIPE_VERSION_002"  # approval_required=False
SKU_CODE = "TEST_SKU_00"

RECIPE_CODE_MACHINE_00 = "TEST_RECIPE_00"   # sku TEST_SKU_00 + MFUK_M00
RECIPE_CODE_MACHINE_99 = "TEST_RECIPE_01"   # sku TEST_SKU_00 + MFUK_M99
VERSION_ON_RECIPE_01 = "TEST_RECIPE_VERSION_011"


async def init_repository_images(
    client: AsyncClient,
    recipe_version_code: str,
    images: list[dict]
) -> Response:
    response = await client.post(
        f"/production/recipe-versions/{recipe_version_code}/repository-images/init",
        json={
            "images": images,
        },
    )
    return response

def simulate_upload(
    fake_storage: FakeStorageClient,
    init_item: dict,
    *,
    data: bytes | None = None,
    content_type: str | None = None,
) -> None:
    """Stand in for browser PUT to upload_url"""
    if not data:
        data = b"x" * 1024
    if not content_type:
        content_type = init_item["content_type"] or "application/octet-stream"
    fake_storage.put_object(
        init_item["bucket"],
        init_item["object_key"],
        data,
        content_type,
    )

async def complete_repository_images(
    client: AsyncClient,
    recipe_version_code: str,
    images: list[dict],
) -> Response:
    response = await client.patch(
        f"/production/recipe-versions/{recipe_version_code}/repository-images/complete",
        json={
            "images": images,
        },
    )
    return response

async def init_upload_complete_one(
    client: AsyncClient,
    fake_storage: FakeStorageClient,
    recipe_version_code: str = DRAFT_RECIPE_VERSION_CODE,
    *,
    filename: str = "ref1.jpg",
    content_type: str = "image/jpeg",
    width: int | None = 1920,
    height: int | None = 1080,
    data: bytes | None = None,
) -> tuple[dict, dict]:
    """
    Full happy path for one image
    Returns (init_item, complete_result_item)
    """
    init_resp = await init_repository_images(
        client,
        recipe_version_code,
        [{"original_filename": filename, "content_type": content_type}],
    )
    assert init_resp.status_code == 201
    init_item = init_resp.json()["images"][0]

    simulate_upload(fake_storage, init_item, data=data, content_type=content_type)

    complete_payload = [{"repository_image_id": init_item["id"], "width": width, "height": height}]
    complete_resp = await complete_repository_images(
        client,
        recipe_version_code,
        complete_payload,
    )
    assert complete_resp.status_code == 200
    complete_result_item = complete_resp.json()["images"][0]
    return init_item, complete_result_item

async def release_recipe_version(client: AsyncClient, version_code: str) -> None:
    """SKU thumbnail and recipe reference_image_url only use RELEASED versions."""
    response = await client.patch(
        f"/production/recipe-versions/{version_code}",
        json={"status": "Released"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "Released"


async def set_reference(client: AsyncClient, repository_image_id: int) -> None:
    response = await client.patch(f"/production/repository-images/{repository_image_id}/set-reference")
    assert response.status_code == 200, response.text


async def init_upload_complete_and_set_reference(
    client: AsyncClient,
    fake_storage: FakeStorageClient,
    recipe_version_code: str,
    *,
    filename: str = "ref.jpg",
    marker_byte: bytes | None = None,
) -> dict:
    """
    Why: Most reference/thumbnail tests need Active + is_reference.
    marker_byte makes each image's object_key/content distinguishable in URLs.
    """
    data = marker_byte if marker_byte is not None else filename.encode()
    init_item, _ = await init_upload_complete_one(
        client,
        fake_storage,
        recipe_version_code=recipe_version_code,
        filename=filename,
        data=data,
    )
    await set_reference(client, init_item["id"])
    return init_item