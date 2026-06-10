import pytest

pytestmark = [pytest.mark.asyncio, pytest.mark.usefixtures("seeded_recipes")]

async def test_superadmin_delete_recipe(authorized_client_superadmin):
    response = await authorized_client_superadmin.delete("/production/recipes/TEST_RECIPE_00")
    assert response.status_code == 204
    response = await authorized_client_superadmin.get("/production/recipes/TEST_RECIPE_00")
    assert response.status_code == 404
    assert response.json()["detail"] == "Recipe with code TEST_RECIPE_00 not found"

async def test_admin_delete_recipe(authorized_client_admin):
    response = await authorized_client_admin.delete("/production/recipes/TEST_RECIPE_00")
    assert response.status_code == 204
    response = await authorized_client_admin.get("/production/recipes/TEST_RECIPE_00")
    assert response.status_code == 404
    assert response.json()["detail"] == "Recipe with code TEST_RECIPE_00 not found"

async def test_user_no_permission_delete_recipe(authorized_client_human_no_role):
    response = await authorized_client_human_no_role.delete("/production/recipes/TEST_RECIPE_00")
    assert response.status_code == 403
    assert response.json()["detail"] == "User does not have permission to access RECIPE_DELETE"

async def test_delete_recipe_not_found(authorized_client_admin):
    response = await authorized_client_admin.delete("/production/recipes/TEST_RECIPE_99")
    assert response.status_code == 404
    assert response.json()["detail"] == "Recipe with code TEST_RECIPE_99 not found"

async def test_delete_recipe_with_deleted_status(authorized_client_admin):
    response = await authorized_client_admin.delete("/production/recipes/TEST_RECIPE_00")
    assert response.status_code == 204
    response = await authorized_client_admin.delete("/production/recipes/TEST_RECIPE_00")
    assert response.status_code == 404
    assert response.json()["detail"] == "Recipe with code TEST_RECIPE_00 not found"

@pytest.mark.usefixtures("seeded_recipe_versions")
async def test_delete_recipe_with_released_recipe_versions(authorized_client_admin):
    # release recipe version 1
    response = await authorized_client_admin.patch(f"/production/recipe-versions/TEST_RECIPE_VERSION_002", json={
        "status": "Released",
    })
    assert response.json()["status"] == "Released"
    assert response.json()["released_at"] is not None

    # delete recipe, should fail
    response = await authorized_client_admin.delete("/production/recipes/TEST_RECIPE_00")
    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot delete a recipe with released recipe versions"
