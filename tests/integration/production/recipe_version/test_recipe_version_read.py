import pytest

from tests.integration.production.recipe_version.helpers import release_recipe_version

pytestmark = [pytest.mark.asyncio, pytest.mark.usefixtures("seeded_recipe_versions")]

async def test_superadmin_get_all_recipe_versions(authorized_client_superadmin):
    response = await authorized_client_superadmin.get("/production/recipes/TEST_RECIPE_00/versions")
    # all recipe versions are not released yet
    assert response.status_code == 200
    assert response.json()["total"] == 0
    assert response.json()["page"] == 1
    assert response.json()["limit"] == 20
    assert response.json()["total_pages"] == 0
    assert len(response.json()["items"]) == 0

    # release the candidate version
    await release_recipe_version(authorized_client_superadmin)
    response = await authorized_client_superadmin.get("/production/recipes/TEST_RECIPE_00/versions")
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["page"] == 1
    assert response.json()["limit"] == 20
    assert response.json()["total_pages"] == 1
    assert len(response.json()["items"]) == 1

async def test_admin_get_all_recipe_versions(authorized_client_admin):
    await release_recipe_version(authorized_client_admin)
    response = await authorized_client_admin.get("/production/recipes/TEST_RECIPE_00/versions")
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["page"] == 1
    assert response.json()["limit"] == 20
    assert response.json()["total_pages"] == 1
    assert len(response.json()["items"]) == 1

async def test_user_no_permission_get_all_recipe_versions(authorized_client_human_no_role):
    response = await authorized_client_human_no_role.get("/production/recipes/TEST_RECIPE_00/versions")
    assert response.status_code == 403
    assert response.json()["detail"] == "User does not have permission to access RECIPE_VERSION_VIEW"

async def test_get_recipe_versions_with_statuses(authorized_client_admin):
    response = await authorized_client_admin.get("/production/recipes/TEST_RECIPE_00/versions?statuses=Released")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 0

async def test_get_recipe_versions_with_multiple_statuses(authorized_client_admin):
    response = await authorized_client_admin.get("/production/recipes/TEST_RECIPE_00/versions?statuses=Draft&statuses=Released")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 2

async def test_get_recipe_versions_with_deleted(authorized_client_admin):
    response = await authorized_client_admin.get(
        "/production/recipes/TEST_RECIPE_00/versions",
        params={
            "include_deleted": True,
            "statuses": ["Draft", "Released"],
        },
    )
    assert response.status_code == 200
    assert len(response.json()["items"]) == 2

    # delete one recipe version
    recipe_version = response.json()["items"][0]
    response = await authorized_client_admin.delete(f"/production/recipe-versions/{recipe_version['version_code']}")
    assert response.status_code == 204

    # get all recipe versions without include_deleted
    response = await authorized_client_admin.get(
        "/production/recipes/TEST_RECIPE_00/versions",
        params={
            "statuses": ["Draft", "Released"],
        },
    )
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1

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

async def test_get_recipe_versions_with_pagination(authorized_client_admin):
    response = await authorized_client_admin.get("/production/recipes/TEST_RECIPE_00/versions?statuses=Draft&page=1&limit=1")
    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert response.json()["page"] == 1
    assert response.json()["limit"] == 1
    assert response.json()["total_pages"] == 2
    assert len(response.json()["items"]) == 1

async def test_get_recipe_versions_search_not_limited_by_page(authorized_client_admin):
    response = await authorized_client_admin.get("/production/recipes/TEST_RECIPE_00/versions?statuses=Draft&search=001&page=1&limit=1")
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["version_code"] == "TEST_RECIPE_VERSION_001"
    assert response.json()["items"][0]["version_name"] == "Test Recipe Version 001"
    assert response.json()["items"][0]["status"] == "Draft"

    response = await authorized_client_admin.get("/production/recipes/TEST_RECIPE_00/versions?statuses=Draft&search=002&page=1&limit=1")
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["version_code"] == "TEST_RECIPE_VERSION_002"