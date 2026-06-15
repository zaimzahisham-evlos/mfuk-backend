import pytest

pytestmark = [pytest.mark.asyncio, pytest.mark.usefixtures("seeded_recipes")]

# Get all recipes
async def test_superadmin_get_all_recipes(authorized_client_superadmin):
    response = await authorized_client_superadmin.get("/production/recipes")
    assert response.status_code == 200
    assert response.json()["total"] == 3
    assert response.json()["page"] == 1
    assert response.json()["limit"] == 20
    assert response.json()["total_pages"] == 1
    assert len(response.json()["items"]) == 3

async def test_admin_get_all_recipes(authorized_client_admin):
    response = await authorized_client_admin.get("/production/recipes")
    assert response.status_code == 200
    assert response.json()["total"] == 3
    assert response.json()["page"] == 1
    assert response.json()["limit"] == 20
    assert response.json()["total_pages"] == 1
    assert len(response.json()["items"]) == 3

async def test_user_no_permission_get_all_recipes(authorized_client_human_no_role):
    response = await authorized_client_human_no_role.get("/production/recipes")
    assert response.status_code == 403
    assert response.json()["detail"] == "User does not have permission to access RECIPE_VIEW"

async def test_get_recipes_with_statuses(authorized_client_admin):
    response = await authorized_client_admin.get("/production/recipes?statuses=Active")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 2

async def test_get_recipes_with_multiple_statuses(authorized_client_admin):
    response = await authorized_client_admin.get("/production/recipes?statuses=Active&statuses=Inactive")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 3

async def test_get_recipes_with_deleted(authorized_client_admin):
    response = await authorized_client_admin.get("/production/recipes")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 3

    # delete one recipe
    recipe = response.json()["items"][0]
    response = await authorized_client_admin.delete(f"/production/recipes/{recipe['recipe_code']}")
    assert response.status_code == 204

    # get all recipes without include_deleted
    response = await authorized_client_admin.get("/production/recipes")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 2

    # get all recipes with include_deleted
    response = await authorized_client_admin.get("/production/recipes?include_deleted=true")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 3

    # get all recipes with include_deleted and statuses=Deleted
    response = await authorized_client_admin.get("/production/recipes?include_deleted=true&statuses=Deleted")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1

async def test_get_recipes_by_sku_id(authorized_client_admin):
    response = await authorized_client_admin.get("/production/skus/TEST_SKU_00")
    sku = response.json()
    response = await authorized_client_admin.get(f"/production/recipes?sku_id={sku['id']}")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 2

async def test_get_recipes_by_machine_id(authorized_client_admin):
    response = await authorized_client_admin.get("/production/machines/MFUK_M00")
    machine = response.json()
    response = await authorized_client_admin.get(f"/production/recipes?machine_id={machine['id']}")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 2

async def test_get_recipes_by_sku_id_and_machine_id(authorized_client_admin):
    response = await authorized_client_admin.get("/production/skus/TEST_SKU_00")
    sku = response.json()
    response = await authorized_client_admin.get("/production/machines/MFUK_M00")
    machine = response.json()
    response = await authorized_client_admin.get(f"/production/recipes?sku_id={sku['id']}&machine_id={machine['id']}")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1

async def test_get_recipe_by_recipe_code(authorized_client_superadmin):
    response = await authorized_client_superadmin.get("/production/recipes/TEST_RECIPE_00")
    assert response.status_code == 200
    assert response.json()["recipe_code"] == "TEST_RECIPE_00"
    assert response.json()["recipe_name"] == "Test Recipe 00"
    assert response.json()["status"] == "Active"

async def test_get_recipe_by_code_not_found(authorized_client_admin):
    response = await authorized_client_admin.get("/production/recipes/TEST_RECIPE_55")
    assert response.status_code == 404
    assert response.json()["detail"] == "Recipe with code TEST_RECIPE_55 not found"

async def test_get_recipe_by_recipe_code_deleted(authorized_client_admin):
    response = await authorized_client_admin.get("/production/recipes/TEST_RECIPE_00")
    assert response.status_code == 200
    assert response.json()["recipe_code"] == "TEST_RECIPE_00"
    assert response.json()["recipe_name"] == "Test Recipe 00"
    assert response.json()["status"] == "Active"
    response = await authorized_client_admin.delete(f"/production/recipes/TEST_RECIPE_00")
    assert response.status_code == 204
    response = await authorized_client_admin.get("/production/recipes/TEST_RECIPE_00")
    assert response.status_code == 404
    assert response.json()["detail"] == "Recipe with code TEST_RECIPE_00 not found"

async def test_user_no_permission_get_recipe_by_recipe_code(authorized_client_human_no_role):
    response = await authorized_client_human_no_role.get("/production/recipes/TEST_RECIPE_00")
    assert response.status_code == 403
    assert response.json()["detail"] == "User does not have permission to access RECIPE_VIEW"

async def test_get_recipes_with_pagination(authorized_client_admin):
    response = await authorized_client_admin.get("/production/recipes?page=1&limit=1")
    assert response.status_code == 200
    assert response.json()["total"] == 3
    assert response.json()["page"] == 1
    assert response.json()["limit"] == 1
    assert response.json()["total_pages"] == 3
    assert len(response.json()["items"]) == 1

async def test_get_recipes_search_not_limited_by_page(authorized_client_admin):
    response = await authorized_client_admin.get("/production/recipes?search=00&page=1&limit=1")
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["recipe_code"] == "TEST_RECIPE_00"
    assert response.json()["items"][0]["recipe_name"] == "Test Recipe 00"
    assert response.json()["items"][0]["status"] == "Active"