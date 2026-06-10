import pytest

pytestmark = [pytest.mark.asyncio, pytest.mark.usefixtures("seeded_recipe_versions")]

async def test_superadmin_get_all_recipe_versions(authorized_client_superadmin):
    response = await authorized_client_superadmin.get("/production/recipes/TEST_RECIPE_00/versions")
    assert response.status_code == 200
    assert len(response.json()) == 2

async def test_admin_get_all_recipe_versions(authorized_client_admin):
    response = await authorized_client_admin.get("/production/recipes/TEST_RECIPE_00/versions")
    assert response.status_code == 200
    assert len(response.json()) == 2

async def test_user_no_permission_get_all_recipe_versions(authorized_client_human_no_role):
    response = await authorized_client_human_no_role.get("/production/recipes/TEST_RECIPE_00/versions")
    assert response.status_code == 403
    assert response.json()["detail"] == "User does not have permission to access RECIPE_VERSION_VIEW"

async def test_get_recipe_versions_with_statuses(authorized_client_admin):
    response = await authorized_client_admin.get("/production/recipes/TEST_RECIPE_00/versions?statuses=Released")
    assert response.status_code == 200
    assert len(response.json()) == 0

async def test_get_recipe_versions_with_multiple_statuses(authorized_client_admin):
    response = await authorized_client_admin.get("/production/recipes/TEST_RECIPE_00/versions?statuses=Draft&statuses=Released")
    assert response.status_code == 200
    assert len(response.json()) == 2

async def test_get_recipe_versions_with_deleted(authorized_client_admin):
    response = await authorized_client_admin.get("/production/recipes/TEST_RECIPE_00/versions?include_deleted=true")
    assert response.status_code == 200
    assert len(response.json()) == 2

    # delete one recipe version
    recipe_version = response.json()[0]
    response = await authorized_client_admin.delete(f"/production/recipe-versions/{recipe_version['version_code']}")
    assert response.status_code == 204

    # get all recipe versions without include_deleted
    response = await authorized_client_admin.get("/production/recipes/TEST_RECIPE_00/versions")
    assert response.status_code == 200
    assert len(response.json()) == 1

async def test_get_recipe_version_by_code(authorized_client_superadmin):
    response = await authorized_client_superadmin.get("/production/recipe-versions/TEST_RECIPE_VERSION_001")
    assert response.status_code == 200
    assert response.json()["version_code"] == "TEST_RECIPE_VERSION_001"
    assert response.json()["version_name"] == "Test Recipe Version 001"
    assert response.json()["status"] == "Draft"

async def test_get_recipe_version_by_code_not_found(authorized_client_admin):
    response = await authorized_client_admin.get("/production/recipe-versions/TEST_RECIPE_VERSION_005")
    assert response.status_code == 404
    assert response.json()["detail"] == "Recipe version with code TEST_RECIPE_VERSION_005 not found"

async def test_get_recipe_version_by_code_deleted(authorized_client_admin):
    response = await authorized_client_admin.get("/production/recipe-versions/TEST_RECIPE_VERSION_001")
    assert response.status_code == 200
    assert response.json()["version_code"] == "TEST_RECIPE_VERSION_001"
    assert response.json()["version_name"] == "Test Recipe Version 001"
    assert response.json()["status"] == "Draft"
    response = await authorized_client_admin.delete(f"/production/recipe-versions/TEST_RECIPE_VERSION_001")
    assert response.status_code == 204
    response = await authorized_client_admin.get("/production/recipe-versions/TEST_RECIPE_VERSION_001")
    assert response.status_code == 404
    assert response.json()["detail"] == "Recipe version with code TEST_RECIPE_VERSION_001 not found"

async def test_user_no_permission_get_recipe_version_by_code(authorized_client_human_no_role):
    response = await authorized_client_human_no_role.get("/production/recipe-versions/TEST_RECIPE_VERSION_001")
    assert response.status_code == 403
    assert response.json()["detail"] == "User does not have permission to access RECIPE_VERSION_VIEW"