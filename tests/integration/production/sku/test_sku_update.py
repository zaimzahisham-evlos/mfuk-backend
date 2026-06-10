import pytest

pytestmark = [pytest.mark.asyncio, pytest.mark.usefixtures("seeded_skus")]

test_payload = {
    "sku_code": "TEST_SKU_00",
    "sku_name": "Test SKU Update",
    "status": "Inactive",
    "description": "Test SKU Update Description",
}

async def test_superadmin_update_sku(authorized_client_superadmin):
    response = await authorized_client_superadmin.get("/production/skus/TEST_SKU_00")
    assert response.status_code == 200
    assert response.json()["sku_code"] == "TEST_SKU_00"
    assert response.json()["sku_name"] == "Test SKU 00"
    assert response.json()["status"] == "Active"
    assert response.json()["description"] is None

    response = await authorized_client_superadmin.patch("/production/skus/TEST_SKU_00", json=test_payload)
    assert response.status_code == 200
    assert response.json()["sku_code"] == "TEST_SKU_00" # sku code is immutable
    assert response.json()["sku_name"] == test_payload["sku_name"]
    assert response.json()["status"] == "Inactive"
    assert response.json()["description"] == test_payload["description"]

async def test_admin_update_sku(authorized_client_admin):
    response = await authorized_client_admin.patch("/production/skus/TEST_SKU_00", json=test_payload)
    assert response.status_code == 200
    assert response.json()["sku_code"] == "TEST_SKU_00" # sku code is immutable
    assert response.json()["sku_name"] == test_payload["sku_name"]
    assert response.json()["status"] == "Inactive"
    assert response.json()["description"] == test_payload["description"]

async def test_user_no_permission_update_sku(authorized_client_human_no_role):
    response = await authorized_client_human_no_role.patch("/production/skus/TEST_SKU_00", json=test_payload)
    assert response.status_code == 403
    assert response.json()["detail"] == "User does not have permission to access SKU_UPDATE"

async def test_update_sku_with_blank_sku_name(authorized_client_admin):
    response = await authorized_client_admin.patch("/production/skus/TEST_SKU_00", json={"sku_name": ""})
    assert response.status_code == 422
    assert response.json()["detail"] == "Value error, Value cannot be blank for field sku_name"

async def test_update_sku_with_invalid_status(authorized_client_admin):
    response = await authorized_client_admin.patch("/production/skus/TEST_SKU_00", json={"status": "Invalid"})
    assert response.status_code == 422
    assert response.json()["detail"] == "Input should be 'Draft', 'Active', 'Inactive', 'Obsolete' or 'Deleted' for field status"

async def test_update_sku_with_deleted_status(authorized_client_admin):
    response = await authorized_client_admin.patch("/production/skus/TEST_SKU_00", json={"status": "Deleted"})
    assert response.status_code == 200
    assert response.json()["sku_code"] == "TEST_SKU_00" # sku code is immutable
    assert response.json()["sku_name"] == "Test SKU 00"
    assert response.json()["status"] == "Deleted"
    assert response.json()["deleted_by_id"] is not None
    assert response.json()["deleted_at"] is not None
    assert response.json()["updated_at"] is not None
    assert response.json()["updated_by_id"] is not None

