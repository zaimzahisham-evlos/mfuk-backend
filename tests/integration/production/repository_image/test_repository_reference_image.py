import pytest

from tests.integration.production.repository_image.helpers import (
    DRAFT_RECIPE_VERSION_CODE,
    RELEASED_CANDIDATE_VERSION_CODE,
    SKU_CODE,
    init_upload_complete_one,
    init_upload_complete_and_set_reference,
    release_recipe_version,
    set_reference,
)

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.usefixtures("seeded_recipe_versions", "fake_storage"),
]


async def test_set_repository_image_reference(authorized_client_admin, fake_storage):
    init_item, _ = await init_upload_complete_one(authorized_client_admin, fake_storage, recipe_version_code=RELEASED_CANDIDATE_VERSION_CODE)

    await set_reference(authorized_client_admin, init_item["id"])

    await release_recipe_version(authorized_client_admin, RELEASED_CANDIDATE_VERSION_CODE)

    # reference image in repository for RELEASED recipe version becomes the thumbnail for SKU
    sku_resp = await authorized_client_admin.get(f"/production/skus/{SKU_CODE}")
    assert sku_resp.status_code == 200
    assert sku_resp.json()["thumbnail_url"]
    assert sku_resp.json()["thumbnail_url"].startswith("http://fake-storage/download/")


async def test_set_repository_image_reference_pending_image_fails(authorized_client_admin):
    init_resp = await authorized_client_admin.post(
        f"/production/recipe-versions/{DRAFT_RECIPE_VERSION_CODE}/repository-images/init",
        json={"images": [{"original_filename": "p.jpg", "content_type": "image/jpeg"}]},
    )
    image_id = init_resp.json()["images"][0]["id"]

    response = await authorized_client_admin.patch(f"/production/repository-images/{image_id}/set-reference")
    assert response.status_code == 400
    assert "not active" in response.json()["detail"].lower()

async def test_set_reference_switches_previous_flag_off(authorized_client_admin, fake_storage):
    """
    DB partial unique index allows one is_reference per recipe version;
    service must clear the old flag when picking a new reference image.
    """
    item_a, _ = await init_upload_complete_one(
        authorized_client_admin, fake_storage, filename="a.jpg"
    )
    item_b, _ = await init_upload_complete_one(
        authorized_client_admin, fake_storage, filename="b.jpg"
    )
    await set_reference(authorized_client_admin, item_a["id"])
    await set_reference(authorized_client_admin, item_b["id"])
    list_resp = await authorized_client_admin.get(
        f"/production/recipe-versions/{DRAFT_RECIPE_VERSION_CODE}/repository-images"
    )
    rows = {row["id"]: row for row in list_resp.json()}
    assert rows[item_a["id"]]["is_reference"] is False
    assert rows[item_b["id"]]["is_reference"] is True

async def test_sku_thumbnail_null_when_only_draft_reference(authorized_client_admin, fake_storage):
    """
    SKU list thumbnail must come from RELEASED version, not draft work-in-progress.
    """
    await init_upload_complete_and_set_reference(
        authorized_client_admin,
        fake_storage,
        DRAFT_RECIPE_VERSION_CODE,
    )
    # NOT released
    sku_resp = await authorized_client_admin.get(f"/production/skus/{SKU_CODE}")
    assert sku_resp.status_code == 200
    assert sku_resp.json()["thumbnail_url"] is None

async def test_sku_thumbnail_null_when_released_but_no_reference(authorized_client_admin, fake_storage):
    """
    Active repository image alone is not enough; is_reference must be set.
    """
    await init_upload_complete_one(
        authorized_client_admin,
        fake_storage,
        recipe_version_code=RELEASED_CANDIDATE_VERSION_CODE,
    )
    await release_recipe_version(authorized_client_admin, RELEASED_CANDIDATE_VERSION_CODE)
    sku_resp = await authorized_client_admin.get(f"/production/skus/{SKU_CODE}")
    assert sku_resp.status_code == 200
    assert sku_resp.json()["thumbnail_url"] is None

async def test_set_reference_on_already_released_version(authorized_client_admin, fake_storage):
    """
    allow changing which Active image is the reference even after release.
    """
    item_a, _ = await init_upload_complete_one(
        authorized_client_admin,
        fake_storage,
        recipe_version_code=RELEASED_CANDIDATE_VERSION_CODE,
        filename="before.jpg",
    )
    item_b, _ = await init_upload_complete_one(
        authorized_client_admin,
        fake_storage,
        recipe_version_code=RELEASED_CANDIDATE_VERSION_CODE,
        filename="after.jpg",
    )
    await set_reference(authorized_client_admin, item_a["id"])
    await release_recipe_version(authorized_client_admin, RELEASED_CANDIDATE_VERSION_CODE)
    await set_reference(authorized_client_admin, item_b["id"])
    list_resp = await authorized_client_admin.get(
        f"/production/recipe-versions/{RELEASED_CANDIDATE_VERSION_CODE}/repository-images"
    )
    rows = {row["id"]: row for row in list_resp.json()}
    assert rows[item_b["id"]]["is_reference"] is True
    assert rows[item_a["id"]]["is_reference"] is False

async def test_set_reference_not_found(authorized_client_admin):
    """Clear 404 when ID does not exist."""
    response = await authorized_client_admin.patch("/production/repository-images/999999/set-reference")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
