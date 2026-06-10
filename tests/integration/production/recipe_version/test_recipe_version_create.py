import pytest

pytestmark = [pytest.mark.asyncio, pytest.mark.usefixtures("seeded_recipe_versions")]

async def get_recipe_version_payload(client):
    response = await client.get("/production/recipes/TEST_RECIPE_10")
    recipe = response.json()
    return {
        "recipe_id": recipe["id"],
        "version_code": "TEST_RECIPE_VERSION_101",
        "version_name": "Test Recipe Version 101",
    }

def assert_recipe_version(response, payload, status_code=201):
    assert response.status_code == status_code
    assert response.json()["version_code"] == payload["version_code"].upper()
    assert response.json()["version_name"] == payload["version_name"]
    assert response.json()["recipe_id"] == payload["recipe_id"]
    assert response.json()["status"] == "Draft"
    assert response.json()["created_by_id"] is not None
    assert response.json()["created_at"] is not None
    assert response.json()["updated_by_id"] is None
    assert response.json()["updated_at"] is None
    assert response.json()["deleted_at"] is None
    assert response.json()["deleted_by_id"] is None

async def test_superadmin_create_recipe_version(authorized_client_superadmin):
    payload = await get_recipe_version_payload(authorized_client_superadmin)
    response = await authorized_client_superadmin.post("/production/recipes/TEST_RECIPE_10/versions", json=payload)
    assert_recipe_version(response, payload)
    assert response.json()["version_no"] == 1
    response = await authorized_client_superadmin.get(f"/production/recipe-versions/{payload['version_code']}")
    assert_recipe_version(response, payload, 200)

async def test_admin_create_recipe_version(authorized_client_admin):
    payload = await get_recipe_version_payload(authorized_client_admin)
    response = await authorized_client_admin.post("/production/recipes/TEST_RECIPE_10/versions", json=payload)
    assert_recipe_version(response, payload)
    assert response.json()["version_no"] == 1
    response = await authorized_client_admin.get(f"/production/recipe-versions/{payload['version_code']}")
    assert_recipe_version(response, payload, 200)

async def test_user_no_permission_create_recipe_version(authorized_client_human_no_role):
    response = await authorized_client_human_no_role.post("/production/recipes/TEST_RECIPE_10/versions", json={})
    assert response.status_code == 403
    assert response.json()["detail"] == "User does not have permission to access RECIPE_VERSION_CREATE"

async def test_create_multiple_recipe_versions(authorized_client_admin):
    payload = await get_recipe_version_payload(authorized_client_admin)
    response = await authorized_client_admin.post("/production/recipes/TEST_RECIPE_10/versions", json=payload)
    assert_recipe_version(response, payload)
    assert response.json()["version_no"] == 1
    response = await authorized_client_admin.get(f"/production/recipe-versions/{payload['version_code']}")
    assert_recipe_version(response, payload, 200)
    payload.update({"version_code": "TEST_RECIPE_VERSION_102"})
    response = await authorized_client_admin.post("/production/recipes/TEST_RECIPE_10/versions", json=payload)
    assert_recipe_version(response, payload)
    assert response.json()["version_no"] == 2

async def test_create_recipe_version_with_blank_version_code(authorized_client_admin):
    payload = await get_recipe_version_payload(authorized_client_admin)
    payload.update({"version_code": " "})
    response = await authorized_client_admin.post("/production/recipes/TEST_RECIPE_10/versions", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"] == "Value error, Value cannot be blank for field version_code"

async def test_create_recipe_version_with_blank_version_name(authorized_client_admin):
    payload = await get_recipe_version_payload(authorized_client_admin)
    payload.update({"version_name": " "})
    response = await authorized_client_admin.post("/production/recipes/TEST_RECIPE_10/versions", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"] == "Value error, Value cannot be blank for field version_name"

async def test_create_recipe_version_with_invalid_version_code_format(authorized_client_admin):
    payload = await get_recipe_version_payload(authorized_client_admin)
    version_codes = ["ic", '"invalid"']
    for version_code in version_codes:
        payload.update({"version_code": version_code})
        response = await authorized_client_admin.post("/production/recipes/TEST_RECIPE_10/versions", json=payload)
        assert response.status_code == 422
        assert response.json()["detail"] == "String should match pattern '^[A-Z0-9._-]{3,80}$' for field version_code"

async def test_create_recipe_version_with_status(authorized_client_admin):
    payload = await get_recipe_version_payload(authorized_client_admin)
    payload.update({"status": "UnderReview"})
    response = await authorized_client_admin.post("/production/recipes/TEST_RECIPE_10/versions", json=payload)
    assert response.status_code == 201
    assert response.json()["status"] == "Draft" # create does not take status, it defaults to Draft

async def test_create_recipe_version_with_duplicate_version_code(authorized_client_admin):
    payload = await get_recipe_version_payload(authorized_client_admin)
    payload.update({"version_code": "TEST_RECIPE_VERSION_001"})
    response = await authorized_client_admin.post("/production/recipes/TEST_RECIPE_10/versions", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Recipe version with code TEST_RECIPE_VERSION_001 already exists"

@pytest.mark.usefixtures("seeded_recipe_versions")
async def test_create_recipe_version_with_source_version_id(authorized_client_admin):
    payload = await get_recipe_version_payload(authorized_client_admin)
    recipe_versions = await authorized_client_admin.get("/production/recipes/TEST_RECIPE_00/versions")
    recipe_version = recipe_versions.json()[0]
    payload.update({"source_version_id": recipe_version["id"], "recipe_id": recipe_version["recipe_id"]})
    response = await authorized_client_admin.post("/production/recipes/TEST_RECIPE_00/versions", json=payload)
    assert response.status_code == 201
    assert response.json()["source_version_id"] == recipe_version["id"]
    assert response.json()["engineering_reason"] == f"Copy of {recipe_version['version_name']}"

@pytest.mark.usefixtures("seeded_recipe_versions")
async def test_create_recipe_version_with_not_found_source_version_id(authorized_client_admin):
    payload = await get_recipe_version_payload(authorized_client_admin)
    payload.update({"source_version_id": 1})
    response = await authorized_client_admin.post("/production/recipes/TEST_RECIPE_00/versions", json=payload)
    assert response.status_code == 404
    assert response.json()["detail"] == "Recipe version with ID 1 not found"

@pytest.mark.usefixtures("seeded_recipe_versions")
async def test_create_recipe_version_with_source_version_id_not_belong_to_recipe(authorized_client_admin):
    payload = await get_recipe_version_payload(authorized_client_admin)
    recipe_00_versions = await authorized_client_admin.get("/production/recipes/TEST_RECIPE_00/versions")
    recipe_00_version = recipe_00_versions.json()[0]
    recipe_01_versions = await authorized_client_admin.get("/production/recipes/TEST_RECIPE_01/versions")
    recipe_01_version = recipe_01_versions.json()[0]    
    payload.update({"source_version_id": recipe_01_version["id"], "recipe_id": recipe_00_version["recipe_id"]})
    response = await authorized_client_admin.post("/production/recipes/TEST_RECIPE_00/versions", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == f"Source recipe version {recipe_01_version['id']} does not belong to recipe {recipe_00_version['recipe_id']}"