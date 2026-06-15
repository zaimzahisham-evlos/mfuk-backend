import pytest

pytestmark = [pytest.mark.asyncio, pytest.mark.usefixtures("seeded_recipes")]

async def get_test_payload(client):
    response = await client.get("/production/skus")
    skus = response.json()["items"]
    response = await client.get("/production/machines")
    machines = response.json()["items"]
    return {
        "recipe_code": "TEST_RECIPE_11",
        "recipe_name": "Test Recipe 11",
        "sku_id": skus[0]["id"],
        "machine_id": machines[0]["id"],
        "status": "Active",
        "description": "Test Recipe 11 description"
    }

def assert_recipe(response, payload, status_code=201):
    assert response.status_code == status_code
    assert response.json()["recipe_code"] == payload["recipe_code"].upper()
    assert response.json()["recipe_name"] == payload["recipe_name"]
    assert response.json()["sku_id"] == payload["sku_id"]
    assert response.json()["machine_id"] == payload["machine_id"]
    assert response.json()["status"] == payload["status"]
    assert response.json()["description"] == payload["description"]
    assert response.json()["created_by_id"] is not None
    assert response.json()["created_at"] is not None
    assert response.json()["updated_by_id"] is None
    assert response.json()["updated_at"] is None
    assert response.json()["deleted_at"] is None
    assert response.json()["deleted_by_id"] is None

# Create a recipe
async def test_superadmin_create_recipe(authorized_client_superadmin):
    payload = await get_test_payload(authorized_client_superadmin)
    response = await authorized_client_superadmin.post("/production/recipes", json=payload)
    assert_recipe(response, payload)
    response = await authorized_client_superadmin.get(f"/production/recipes/{payload['recipe_code']}")
    assert_recipe(response, payload, 200)

async def test_admin_create_recipe(authorized_client_admin):
    payload = await get_test_payload(authorized_client_admin)
    response = await authorized_client_admin.post("/production/recipes", json=payload)
    assert_recipe(response, payload)
    response = await authorized_client_admin.get(f"/production/recipes/{payload['recipe_code']}")
    assert_recipe(response, payload, 200)

async def test_user_no_permission_create_recipe(authorized_client_human_no_role):
    response = await authorized_client_human_no_role.post("/production/recipes", json={})
    assert response.status_code == 403
    assert response.json()["detail"] == "User does not have permission to access RECIPE_CREATE"

async def test_create_recipe_with_blank_recipe_code(authorized_client_admin):
    payload = await get_test_payload(authorized_client_admin)
    payload.update({"recipe_code": " "})
    response = await authorized_client_admin.post("/production/recipes", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"] == "Value error, Value cannot be blank for field recipe_code"

async def test_create_recipe_with_blank_recipe_name(authorized_client_admin):
    payload = await get_test_payload(authorized_client_admin)
    payload.update({"recipe_name": " "})
    response = await authorized_client_admin.post("/production/recipes", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"] == "Value error, Value cannot be blank for field recipe_name"

async def test_create_recipe_with_invalid_recipe_code_format(authorized_client_admin):
    payload = await get_test_payload(authorized_client_admin)
    recipe_codes = ["ic", '"invalid"']
    for recipe_code in recipe_codes:
        payload.update({"recipe_code": recipe_code})
        response = await authorized_client_admin.post("/production/recipes", json=payload)
        assert response.status_code == 422
        assert response.json()["detail"] == "String should match pattern '^[A-Z0-9._-]{3,80}$' for field recipe_code"

async def test_create_recipe_with_deleted_status(authorized_client_admin):
    payload = await get_test_payload(authorized_client_admin)
    payload.update({"status": "Deleted"})
    response = await authorized_client_admin.post("/production/recipes", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot create a recipe with status Deleted"

async def test_create_recipe_with_duplicate_recipe_code(authorized_client_admin):
    payload = await get_test_payload(authorized_client_admin)
    payload.update({"recipe_code": "TEST_RECIPE_00"})
    response = await authorized_client_admin.post("/production/recipes", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Recipe with code TEST_RECIPE_00 already exists"

async def test_create_recipe_with_duplicate_sku_and_machine(authorized_client_admin):
    # ensures one recipe per SKU and machine is enforced
    payload = await get_test_payload(authorized_client_admin)
    response = await authorized_client_admin.get("/production/skus/TEST_SKU_00")
    sku = response.json()
    response = await authorized_client_admin.get("/production/machines/MFUK_M00")
    machine = response.json()
    payload.update({"sku_id": sku["id"], "machine_id": machine["id"]})
    response = await authorized_client_admin.post("/production/recipes", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == f"Recipe with SKU {sku['id']} and machine {machine['id']} already exists"