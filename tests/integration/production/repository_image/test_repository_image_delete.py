import pytest

from tests.integration.production.repository_image.helpers import (
    DRAFT_RECIPE_VERSION_CODE,
    SKU_CODE,
    init_upload_complete_one,
)

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.usefixtures("seeded_recipe_versions", "fake_storage"),
]


async def test_delete_repository_image(authorized_client_admin, fake_storage):
    init_item, _ = await init_upload_complete_one(authorized_client_admin, fake_storage)
    image_id = init_item["id"]
    bucket, key = init_item["bucket"], init_item["object_key"]

    assert (bucket, key) in fake_storage.objects

    delete_resp = await authorized_client_admin.delete(
        f"/production/repository-images",
        params={"repository_image_ids": [image_id]},
    )
    assert delete_resp.status_code == 200
    assert delete_resp.content.decode("utf-8") == f"Deleted 1 repository images"
    assert (bucket, key) not in fake_storage.objects

    list_resp = await authorized_client_admin.get(
        f"/production/recipe-versions/{DRAFT_RECIPE_VERSION_CODE}/repository-images"
    )
    assert all(row["id"] != image_id for row in list_resp.json())


async def test_delete_on_released_recipe_version(authorized_client_admin, fake_storage):
    init_item, _ = await init_upload_complete_one(
        authorized_client_admin,
        fake_storage,
        recipe_version_code="TEST_RECIPE_VERSION_002",
    )

    release_resp = await authorized_client_admin.patch(
        "/production/recipe-versions/TEST_RECIPE_VERSION_002",
        json={"status": "Released"},
    )
    assert release_resp.status_code == 200

    delete_resp = await authorized_client_admin.delete(
        "/production/repository-images",
        params={"repository_image_ids": [init_item["id"]]},
    )
    assert delete_resp.status_code == 400
    assert "released" in delete_resp.json()["detail"].lower()

async def test_delete_reference_image(authorized_client_admin, fake_storage):
    init_item, _ = await init_upload_complete_one(
        authorized_client_admin,
        fake_storage,
        recipe_version_code="TEST_RECIPE_VERSION_002",
    )
    set_resp = await authorized_client_admin.patch(f"/production/repository-images/{init_item['id']}/set-reference")
    assert set_resp.status_code == 200

    delete_resp = await authorized_client_admin.delete(
        "/production/repository-images",
        params={"repository_image_ids": [init_item["id"]]},
    )
    assert delete_resp.status_code == 200
    assert delete_resp.content.decode("utf-8") == f"Deleted 0 repository images and skipped 1 reference repository images with ids [{init_item['id']}]"


async def test_user_no_permission_delete(authorized_client_human_no_role):
    """Delete removes storage objects; must require REPOSITORY_IMAGE_DELETE."""
    response = await authorized_client_human_no_role.delete(
        "/production/repository-images",
        params={"repository_image_ids": [1]},
    )
    assert response.status_code == 403
    assert "REPOSITORY_IMAGE_DELETE" in response.json()["detail"]


async def test_delete_unknown_id_is_idempotent(authorized_client_admin):
    """
    Documents intentional behavior — unknown IDs are ignored, still 200.
    """
    response = await authorized_client_admin.delete(
        "/production/repository-images",
        params={"repository_image_ids": [999999]},
    )
    assert response.status_code == 200
    assert response.text == "Deleted 1 repository images"