"""
Tests for derived URLs: Recipe.reference_image_url and SKU.thumbnail_url rules.
"""
import pytest

from tests.integration.production.repository_image.helpers import (
    RECIPE_CODE_MACHINE_00,
    RECIPE_CODE_MACHINE_99,
    RELEASED_CANDIDATE_VERSION_CODE,
    SKU_CODE,
    VERSION_ON_RECIPE_01,
    init_upload_complete_and_set_reference,
    release_recipe_version,
)

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.usefixtures("seeded_recipe_versions", "fake_storage"),
]


async def test_recipe_reference_image_url_after_release(authorized_client_admin, fake_storage):
    """
    Recipe cards on SKU detail page show each machine's reference from its RELEASED version.
    """
    init_item = await init_upload_complete_and_set_reference(
        authorized_client_admin,
        fake_storage,
        RELEASED_CANDIDATE_VERSION_CODE,
        filename="recipe-ref.jpg",
        marker_byte=b"recipe-ref-marker",
    )
    await release_recipe_version(authorized_client_admin, RELEASED_CANDIDATE_VERSION_CODE)

    recipe_resp = await authorized_client_admin.get(f"/production/recipes/{RECIPE_CODE_MACHINE_00}")
    assert recipe_resp.status_code == 200
    assert recipe_resp.json()["reference_image_url"]
    assert init_item["object_key"] in recipe_resp.json()["reference_image_url"]


async def test_recipe_reference_image_url_null_when_not_released(authorized_client_admin, fake_storage):
    """Draft reference must not appear on recipe list until version is released."""
    await init_upload_complete_and_set_reference(
        authorized_client_admin,
        fake_storage,
        RELEASED_CANDIDATE_VERSION_CODE,
    )

    recipe_resp = await authorized_client_admin.get(f"/production/recipes/{RECIPE_CODE_MACHINE_00}")
    assert recipe_resp.status_code == 200
    assert recipe_resp.json()["reference_image_url"] is None


async def test_sku_thumbnail_uses_lowest_machine_id_recipe(authorized_client_admin, fake_storage):
    """
    One SKU, two machines/recipes — thumbnail picks reference from recipe
    with lowest machine_id (MFUK_M00 / TEST_RECIPE_00), not the other machine.
    """
    # Machine 99 recipe: release with a distinguishable reference first
    item_m99 = await init_upload_complete_and_set_reference(
        authorized_client_admin,
        fake_storage,
        VERSION_ON_RECIPE_01,
        filename="m99.jpg",
        marker_byte=b"machine-99-marker",
    )
    await release_recipe_version(authorized_client_admin, VERSION_ON_RECIPE_01)

    # Machine 00 recipe: release after — should win for SKU thumbnail
    item_m00 = await init_upload_complete_and_set_reference(
        authorized_client_admin,
        fake_storage,
        RELEASED_CANDIDATE_VERSION_CODE,
        filename="m00.jpg",
        marker_byte=b"machine-00-marker",
    )
    await release_recipe_version(authorized_client_admin, RELEASED_CANDIDATE_VERSION_CODE)

    sku_resp = await authorized_client_admin.get(f"/production/skus/{SKU_CODE}")
    assert sku_resp.status_code == 200
    thumbnail_url = sku_resp.json()["thumbnail_url"]
    assert thumbnail_url
    assert item_m00["object_key"] in thumbnail_url
    assert item_m99["object_key"] not in thumbnail_url