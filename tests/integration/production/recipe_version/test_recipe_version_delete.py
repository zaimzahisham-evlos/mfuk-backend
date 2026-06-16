import pytest

pytestmark = [pytest.mark.asyncio, pytest.mark.usefixtures("seeded_recipe_versions")]

async def test_superadmin_delete_recipe_version(authorized_client_superadmin):
    response = await authorized_client_superadmin.delete("/production/recipe-versions/TEST_RECIPE_VERSION_001")
    assert response.status_code == 204
    response = await authorized_client_superadmin.get("/production/recipe-versions/TEST_RECIPE_VERSION_001")
    assert response.status_code == 404
    assert response.json()["detail"] == "Recipe version with code TEST_RECIPE_VERSION_001 not found"

async def test_admin_delete_recipe_version(authorized_client_admin):
    response = await authorized_client_admin.delete("/production/recipe-versions/TEST_RECIPE_VERSION_001")
    assert response.status_code == 204
    response = await authorized_client_admin.get("/production/recipe-versions/TEST_RECIPE_VERSION_001")
    assert response.status_code == 404
    assert response.json()["detail"] == "Recipe version with code TEST_RECIPE_VERSION_001 not found"

async def test_user_no_permission_delete_recipe_version(authorized_client_human_no_role):
    response = await authorized_client_human_no_role.delete("/production/recipe-versions/TEST_RECIPE_VERSION_001")
    assert response.status_code == 403
    assert response.json()["detail"] == "User does not have permission to access RECIPE_VERSION_DELETE"

async def test_delete_recipe_version_not_found(authorized_client_admin):
    response = await authorized_client_admin.delete("/production/recipe-versions/TEST_RECIPE_VERSION_99")
    assert response.status_code == 404
    assert response.json()["detail"] == "Recipe version with code TEST_RECIPE_VERSION_99 not found"

async def test_delete_recipe_version_with_deleted_status(authorized_client_admin):
    response = await authorized_client_admin.delete("/production/recipe-versions/TEST_RECIPE_VERSION_001")
    assert response.status_code == 204
    response = await authorized_client_admin.delete("/production/recipe-versions/TEST_RECIPE_VERSION_001")
    assert response.status_code == 404
    assert response.json()["detail"] == "Recipe version with code TEST_RECIPE_VERSION_001 not found"

async def test_delete_recipe_version_with_released_status(authorized_client_admin):
    # release recipe version 1. Note: approval is required for released.
    response = await authorized_client_admin.patch(f"/production/recipe-versions/TEST_RECIPE_VERSION_001", json={
        "status": "Approved",
    })
    response = await authorized_client_admin.patch(f"/production/recipe-versions/TEST_RECIPE_VERSION_001", json={
        "status": "Released",
    })
    assert response.json()["status"] == "Released"
    assert response.json()["released_at"] is not None

    # delete recipe version 1, should fail
    response = await authorized_client_admin.delete("/production/recipe-versions/TEST_RECIPE_VERSION_001")
    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot delete a released recipe version"
