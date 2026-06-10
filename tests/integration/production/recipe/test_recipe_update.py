import pytest

pytestmark = [pytest.mark.asyncio, pytest.mark.usefixtures("seeded_recipes")]

test_payload = {
    "recipe_code": "TEST_RECIPE_00_UPDATE",
    "recipe_name": "test recipe update",
    "status": "Inactive",
    "description": "Test Recipe Update Description",
}

def assert_recipe_updated(response, payload):
    assert response.status_code == 200
    assert response.json()["recipe_name"] == payload["recipe_name"]
    assert response.json()["status"] == payload["status"]
    assert response.json()["description"] == payload["description"]
    assert response.json()["updated_at"] is not None
    assert response.json()["updated_by_id"] is not None

async def test_superadmin_update_recipe(authorized_client_superadmin):
    payload = test_payload.copy()
    response = await authorized_client_superadmin.patch("/production/recipes/TEST_RECIPE_00", json=payload)
    assert_recipe_updated(response, payload)
    assert response.json()["recipe_code"] == "TEST_RECIPE_00" # recipe code is immutable

async def test_admin_update_recipe(authorized_client_admin):
    payload = test_payload.copy()
    response = await authorized_client_admin.patch("/production/recipes/TEST_RECIPE_00", json=payload)
    assert_recipe_updated(response, payload)
    assert response.json()["recipe_code"] == "TEST_RECIPE_00" # recipe code is immutable

async def test_user_no_permission_update_recipe(authorized_client_human_no_role):
    payload = test_payload.copy()
    response = await authorized_client_human_no_role.patch("/production/recipes/TEST_RECIPE_00", json=payload)
    assert response.status_code == 403
    assert response.json()["detail"] == "User does not have permission to access RECIPE_UPDATE"

async def test_update_recipe_with_blank_recipe_name(authorized_client_admin):
    payload = test_payload.copy()
    payload.update({"recipe_name": " "})
    response = await authorized_client_admin.patch("/production/recipes/TEST_RECIPE_00", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"] == "Value error, Value cannot be blank for field recipe_name"

async def test_update_recipe_with_invalid_status(authorized_client_admin):
    payload = test_payload.copy()
    payload.update({"status": "Invalid"})
    response = await authorized_client_admin.patch("/production/recipes/TEST_RECIPE_00", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"] == "Input should be 'Active', 'Inactive', 'Obsolete' or 'Deleted' for field status"

async def test_update_recipe_with_deleted_status(authorized_client_admin):
    payload = test_payload.copy()
    payload.update({"status": "Deleted"})
    response = await authorized_client_admin.patch("/production/recipes/TEST_RECIPE_00", json=payload)
    assert response.status_code == 200
    assert response.json()["recipe_code"] == "TEST_RECIPE_00" # recipe code is immutable
    assert response.json()["recipe_name"] == payload["recipe_name"]
    assert response.json()["status"] == "Deleted"
    assert response.json()["deleted_by_id"] is not None
    assert response.json()["deleted_at"] is not None
    assert response.json()["updated_at"] is not None
    assert response.json()["updated_by_id"] is not None