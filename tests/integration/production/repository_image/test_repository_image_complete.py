import pytest 

from app.core.config import settings
from tests.fakes.storage import FakeStorageClient
from tests.integration.production.repository_image.helpers import *

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.usefixtures("seeded_recipe_versions", "fake_storage"),
]


async def test_init_upload_complete_one_image(authorized_client_admin, fake_storage):
    init_item, complete_result_item = await init_upload_complete_one(
        authorized_client_admin,
        fake_storage,
        recipe_version_code=DRAFT_RECIPE_VERSION_CODE,
        filename="ref1.jpg",
        content_type="image/jpeg",
        width=1920,
        height=1080,
    )
    assert init_item["original_filename"] == "ref1.jpg"
    assert complete_result_item["status"] == "Active"
    assert complete_result_item["byte_size"] == 1024
    assert complete_result_item["content_type"] == "image/jpeg"
    assert complete_result_item["download_url"].startswith("http://fake-storage/download/")

    response = await authorized_client_admin.get(
        f"/production/recipe-versions/{DRAFT_RECIPE_VERSION_CODE}/repository-images",
    )
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["original_filename"] == "ref1.jpg"
    assert response.json()["items"][0]["status"] == "Active"
    assert response.json()["items"][0]["byte_size"] == 1024
    assert response.json()["items"][0]["content_type"] == "image/jpeg"
    assert response.json()["items"][0]["download_url"].startswith("http://fake-storage/download/")
    assert response.json()["items"][0]["bucket"]
    assert response.json()["items"][0]["object_key"]
    assert response.json()["items"][0]["width"] == 1920
    assert response.json()["items"][0]["height"] == 1080

async def test_complete_without_upload(authorized_client_admin, fake_storage):
    response = await init_repository_images(
        authorized_client_admin,
        DRAFT_RECIPE_VERSION_CODE,
        [{"original_filename": "ref1.jpg", "content_type": "image/jpeg"}],
    )
    assert response.status_code == 201
    image_id = response.json()["images"][0]["id"]

    # skips upload; no simulate_upload -> head() 404 -> 400
    response = await complete_repository_images(
        authorized_client_admin,
        DRAFT_RECIPE_VERSION_CODE,
        [{"repository_image_id": image_id}],
    )
    assert response.status_code == 400
    assert response.json()["detail"] == f"Uploaded object not found for repository image {image_id}"

async def test_complete_idempotent_when_already_active(authorized_client_admin, fake_storage):
    init_item, _ = await init_upload_complete_one(
        authorized_client_admin,
        fake_storage
    )
    
    second = await complete_repository_images(
        authorized_client_admin,
        DRAFT_RECIPE_VERSION_CODE,
        [{"repository_image_id": init_item["id"]}],
    )
    assert second.status_code == 200
    assert second.json()["images"][0]["status"] == "Active"
    assert second.json()["images"][0]["byte_size"] == 1024
    assert second.json()["images"][0]["content_type"] == "image/jpeg"
    assert second.json()["images"][0]["download_url"].startswith("http://fake-storage/download/")

async def test_complete_unsupported_content_type_from_storage(authorized_client_admin, fake_storage):
    init = await init_repository_images(
        authorized_client_admin,
        DRAFT_RECIPE_VERSION_CODE,
        [{"original_filename": "ref1.jpg", "content_type": "image/jpeg"}],
    )
    assert init.status_code == 201
    image = init.json()["images"][0]

    #client said jpeg at init but "uploaded" object reports pdf at head time
    simulate_upload(
        fake_storage,
        image,
        data=b"x" * 1024,
        content_type="application/pdf",
    )

    complete = await complete_repository_images(
        authorized_client_admin,
        DRAFT_RECIPE_VERSION_CODE,
        [{"repository_image_id": image["id"]}],
    )
    assert complete.status_code == 400
    assert complete.json()["detail"] == f"Repository image {image['id']} has an unsupported content type: application/pdf. Allowed content types are {', '.join(settings.ALLOWED_IMAGE_CONTENT_TYPES)}"

async def test_complete_too_large_from_storage(authorized_client_admin, fake_storage):
    init = await init_repository_images(
        authorized_client_admin,
        DRAFT_RECIPE_VERSION_CODE,
        [{"original_filename": "ref1.jpg", "content_type": "image/jpeg"}],
    )
    assert init.status_code == 201
    image = init.json()["images"][0]

    #client said jpeg at init but "uploaded" object reports 100MB at head time
    simulate_upload(
        fake_storage,
        image,
        data=b"x" * (settings.MAX_REPOSITORY_IMAGE_BYTES + 1),
        content_type="image/jpeg",
    )

    complete = await complete_repository_images(
        authorized_client_admin,
        DRAFT_RECIPE_VERSION_CODE,
        [{"repository_image_id": image["id"]}],
    )
    assert complete.status_code == 400
    assert complete.json()["detail"] == f"Repository image {image['id']} is too large. Maximum repository image size is 100 MB"

async def test_complete_missing_repository_image_id(authorized_client_admin, fake_storage):
    response = await complete_repository_images(
        authorized_client_admin,
        DRAFT_RECIPE_VERSION_CODE,
        [{"repository_image_id": 9}],
    )
    assert response.status_code == 400
    assert response.json()["detail"] == f"Repository image IDs not found for recipe version {DRAFT_RECIPE_VERSION_CODE}: [9]"

async def test_complete_bulk_two_images(authorized_client_admin, fake_storage):
    """
    Production UI uploads many files; complete must handle multiple IDs in one PATCH.
    """
    init_resp = await init_repository_images(
        authorized_client_admin,
        DRAFT_RECIPE_VERSION_CODE,
        [
            {"original_filename": "a.jpg", "content_type": "image/jpeg"},
            {"original_filename": "b.png", "content_type": "image/png"},
        ],
    )
    assert init_resp.status_code == 201
    items = init_resp.json()["images"]
    assert len(items) == 2

    for item in items:
        simulate_upload(fake_storage, item)

    complete_resp = await complete_repository_images(
        authorized_client_admin,
        DRAFT_RECIPE_VERSION_CODE,
        [
            {"repository_image_id": items[0]["id"], "width": 100, "height": 200},
            {"repository_image_id": items[1]["id"], "width": 300, "height": 400},
        ],
    )
    assert complete_resp.status_code == 200
    results = {row["id"]: row for row in complete_resp.json()["images"]}
    assert results[items[0]["id"]]["status"] == "Active"
    assert results[items[1]["id"]]["status"] == "Active"
    assert results[items[0]["id"]]["download_url"]
    assert results[items[1]["id"]]["download_url"]

    list_resp = await authorized_client_admin.get(
        f"/production/recipe-versions/{DRAFT_RECIPE_VERSION_CODE}/repository-images"
    )
    assert list_resp.status_code == 200
    by_id = {row["id"]: row for row in list_resp.json()["items"]}
    assert by_id[items[0]["id"]]["width"] == 100
    assert by_id[items[1]["id"]]["height"] == 400


async def test_user_no_permission_complete(authorized_client_human_no_role):
    """RBAC must gate the complete step, not only init."""
    response = await authorized_client_human_no_role.patch(
        f"/production/recipe-versions/{DRAFT_RECIPE_VERSION_CODE}/repository-images/complete",
        json={"images": [{"repository_image_id": 1}]},
    )
    assert response.status_code == 403
    assert "REPOSITORY_IMAGE_UPDATE" in response.json()["detail"]