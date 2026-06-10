import pytest

pytestmark = pytest.mark.asyncio

test_payload = {
    "sku_code": "test_sku_create",
    "sku_name": "Test SKU Create",
    "status": "Active",
}

def assert_sku_created(response, payload, status_code=201):
    assert response.status_code == status_code
    assert response.json()["sku_code"] == payload["sku_code"].upper()
    assert response.json()["sku_name"] == payload["sku_name"]
    assert response.json()["status"] == payload["status"]
    assert response.json()["created_by_id"] is not None
    assert response.json()["created_at"] is not None
    assert response.json()["updated_at"] is None
    assert response.json()["deleted_at"] is None
    assert response.json()["deleted_by_id"] is None

async def test_superadmin_create_sku(authorized_client_superadmin):
    response = await authorized_client_superadmin.post("/production/skus", json=test_payload)
    assert_sku_created(response, test_payload)
    result = await authorized_client_superadmin.get(f"/production/skus/{test_payload['sku_code']}")
    assert_sku_created(result, test_payload, 200)

async def test_admin_create_sku(authorized_client_admin):
    response = await authorized_client_admin.post("/production/skus", json=test_payload)
    assert_sku_created(response, test_payload)
    result = await authorized_client_admin.get(f"/production/skus/{test_payload['sku_code']}")
    assert_sku_created(result, test_payload, 200)

async def test_user_no_permission_create_sku(authorized_client_human_no_role):
    response = await authorized_client_human_no_role.post("/production/skus", json=test_payload)
    assert response.status_code == 403

async def test_create_sku_with_blank_sku_code(authorized_client_admin):
    payload = test_payload.copy()
    payload["sku_code"] = " "
    response = await authorized_client_admin.post("/production/skus", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"] == "Value error, Value cannot be blank for field sku_code"

async def test_create_sku_with_blank_sku_name(authorized_client_admin):
    payload = test_payload.copy()
    payload["sku_name"] = " "
    response = await authorized_client_admin.post("/production/skus", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"] == "Value error, Value cannot be blank for field sku_name"

async def test_create_sku_with_invalid_sku_code_format(authorized_client_admin):
    payload = test_payload.copy()
    sku_codes = ["IC", "INVALID-CODE", '"INVALID"', "ic", "invalid-code", '"invalid']
    for sku_code in sku_codes:
        payload["sku_code"] = sku_code
        response = await authorized_client_admin.post("/production/skus", json=payload)
        assert response.status_code == 422
        assert response.json()["detail"] == "String should match pattern '^[A-Z0-9_]{3,80}$' for field sku_code"

async def test_create_sku_with_deleted_status(authorized_client_admin):
    payload = test_payload.copy()
    payload["status"] = "Deleted"
    response = await authorized_client_admin.post("/production/skus", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot create an SKU with status Deleted"

async def test_create_sku_with_duplicate_sku_code(authorized_client_admin):
    payload = test_payload.copy()
    response = await authorized_client_admin.post("/production/skus", json=payload)
    assert response.status_code == 201
    response = await authorized_client_admin.post("/production/skus", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "SKU with code TEST_SKU_CREATE already exists"

async def test_create_sku_with_invalid_status(authorized_client_admin):
    payload = test_payload.copy()
    payload["status"] = "Invalid"
    response = await authorized_client_admin.post("/production/skus", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"] == "Input should be 'Draft', 'Active', 'Inactive', 'Obsolete' or 'Deleted' for field status"

async def test_create_sku_with_description(authorized_client_admin):
    payload = test_payload.copy()
    payload["description"] = "Test SKU Description"
    response = await authorized_client_admin.post("/production/skus", json=payload)
    assert response.status_code == 201
    assert response.json()["description"] == payload["description"]
    response = await authorized_client_admin.get(f"/production/skus/{test_payload['sku_code']}")
    assert response.json()["description"] == payload["description"]

