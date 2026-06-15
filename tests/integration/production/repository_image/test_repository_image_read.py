import pytest

from tests.integration.production.repository_image.helpers import (
    DRAFT_RECIPE_VERSION_CODE,
    init_upload_complete_one,
)

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.usefixtures("seeded_recipe_versions", "fake_storage"),
]


async def test_list_active_has_download_url(authorized_client_admin, fake_storage):
    init_item, _ = await init_upload_complete_one(authorized_client_admin, fake_storage)

    response = await authorized_client_admin.get(
        f"/production/recipe-versions/{DRAFT_RECIPE_VERSION_CODE}/repository-images"
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["page"] == 1
    assert response.json()["limit"] == 20
    assert response.json()["total_pages"] == 1
    row = next(i for i in response.json()["items"] if i["id"] == init_item["id"])
    assert row["status"] == "Active"
    assert row["download_url"]


async def test_list_pending_has_no_download_url(authorized_client_admin):
    init_resp = await authorized_client_admin.post(
        f"/production/recipe-versions/{DRAFT_RECIPE_VERSION_CODE}/repository-images/init",
        json={"images": [{"original_filename": "pending.jpg", "content_type": "image/jpeg"}]},
    )
    assert init_resp.status_code == 201
    image_id = init_resp.json()["images"][0]["id"]

    response = await authorized_client_admin.get(
        f"/production/recipe-versions/{DRAFT_RECIPE_VERSION_CODE}/repository-images"
    )
    assert response.status_code == 200
    row = next(i for i in response.json()["items"] if i["id"] == image_id)
    assert row["status"] == "Pending"
    assert row["download_url"] is None


async def test_user_no_permission_list(authorized_client_human_no_role):
    response = await authorized_client_human_no_role.get(
        f"/production/recipe-versions/{DRAFT_RECIPE_VERSION_CODE}/repository-images"
    )
    assert response.status_code == 403
    assert "REPOSITORY_IMAGE_VIEW" in response.json()["detail"]

async def test_list_filter_statuses_pending(authorized_client_admin, fake_storage):
    """
    Frontend may list only Pending slots still awaiting upload.
    """
    pending_item, _ = await init_upload_complete_one(authorized_client_admin, fake_storage)
    # second image stays Pending
    init_resp = await authorized_client_admin.post(
        f"/production/recipe-versions/{DRAFT_RECIPE_VERSION_CODE}/repository-images/init",
        json={"images": [{"original_filename": "still-pending.jpg", "content_type": "image/jpeg"}]},
    )
    assert init_resp.status_code == 201
    pending_only_id = init_resp.json()["images"][0]["id"]

    response = await authorized_client_admin.get(
        f"/production/recipe-versions/{DRAFT_RECIPE_VERSION_CODE}/repository-images",
        params={"statuses": "Pending"},
    )
    assert response.status_code == 200
    ids = {row["id"] for row in response.json()["items"]}
    assert pending_only_id in ids
    assert pending_item["id"] not in ids
    for row in response.json()["items"]:
        assert row["status"] == "Pending"
        assert row["download_url"] is None

async def test_get_repository_images_with_pagination(authorized_client_admin, fake_storage):
    init_item1, _ = await init_upload_complete_one(authorized_client_admin, fake_storage)
    init_item2, _ = await init_upload_complete_one(authorized_client_admin, fake_storage, filename="ref2.jpg")
    response = await authorized_client_admin.get(f"/production/recipe-versions/{DRAFT_RECIPE_VERSION_CODE}/repository-images?page=1&limit=1")
    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert response.json()["page"] == 1
    assert response.json()["limit"] == 1
    assert response.json()["total_pages"] == 2
    assert len(response.json()["items"]) == 1

async def test_get_repository_images_search_not_limited_by_page(authorized_client_admin, fake_storage):
    init_item1, _ = await init_upload_complete_one(authorized_client_admin, fake_storage)
    init_item2, _ = await init_upload_complete_one(authorized_client_admin, fake_storage, filename="ref2.jpg")
    response = await authorized_client_admin.get(f"/production/recipe-versions/{DRAFT_RECIPE_VERSION_CODE}/repository-images?search=ref1&page=1&limit=1")
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["page"] == 1
    assert response.json()["limit"] == 1
    assert response.json()["total_pages"] == 1
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["original_filename"] == "ref1.jpg"