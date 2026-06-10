import pytest

pytestmark = pytest.mark.asyncio

test_payload = {
    "permission_name": "Test Permission Update",
    "module": "permission",
    "category": "update"
}

def assert_permission_updated(response, payload):
    assert response.status_code == 200
    assert response.json()["permission_name"] == payload["permission_name"]
    assert response.json()["module"] == payload["module"].title()
    assert response.json()["category"] == payload["category"]
    assert response.json()["status"] == "Active"
    assert response.json()["description"] is None
    assert response.json()["is_system_permission"] is False
    assert response.json()["updated_at"] is not None

async def test_superadmin_update_permission(authorized_client_superadmin):
    response = await authorized_client_superadmin.patch("/authorization/permissions/permission_update", json=test_payload)
    assert_permission_updated(response, test_payload)

async def test_user_no_permission_update_permission(authorized_client_human_no_role):
    response = await authorized_client_human_no_role.patch("/authorization/permissions/permission_update", json=test_payload)
    assert response.status_code == 403
    assert response.json()["detail"] == "User does not have permission to access PERMISSION_UPDATE"

async def test_rbac_manager_update_permission(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.patch("/authorization/permissions/permission_update", json=test_payload)
    assert_permission_updated(response, test_payload)

async def test_update_permission_with_blank_permission_name(authorized_client_rbac_manager):
    payload = test_payload.copy()
    payload["permission_name"] = " "
    response = await authorized_client_rbac_manager.patch("/authorization/permissions/permission_update", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"] == "Value error, Value cannot be blank for field permission_name"

async def test_update_permission_with_blank_module(authorized_client_rbac_manager):
    payload = test_payload.copy()
    payload["module"] = " "
    response = await authorized_client_rbac_manager.patch("/authorization/permissions/permission_update", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"] == "Value error, Value cannot be blank for field module"

async def test_update_permission_with_blank_category(authorized_client_rbac_manager):
    payload = test_payload.copy()
    payload["category"] = " "
    response = await authorized_client_rbac_manager.patch("/authorization/permissions/permission_update", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"] == "Input should be 'view', 'create', 'update', 'delete', 'approve', 'export', 'assign', 'revoke', 'execute' or 'override' for field category"

async def test_update_permission_with_invalid_category(authorized_client_rbac_manager):
    payload = test_payload.copy()
    payload["category"] = "invalid"
    response = await authorized_client_rbac_manager.patch("/authorization/permissions/permission_update", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"] == "Input should be 'view', 'create', 'update', 'delete', 'approve', 'export', 'assign', 'revoke', 'execute' or 'override' for field category"

async def test_update_permission_with_deleted_status(authorized_client_rbac_manager):
    payload = test_payload.copy()
    payload["status"] = "Deleted"
    response = await authorized_client_rbac_manager.patch("/authorization/permissions/permission_update", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "Deleted"
    assert response.json()["updated_at"] is not None
    assert response.json()["updated_by_id"] is not None
    assert response.json()["deleted_at"] is not None
    assert response.json()["deleted_by_id"] is not None

async def test_update_permission_with_invalid_status(authorized_client_rbac_manager):
    payload = test_payload.copy()
    payload["status"] = "invalid"
    response = await authorized_client_rbac_manager.patch("/authorization/permissions/permission_update", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"] == "Input should be 'Active', 'Inactive', 'Deleted' or 'Deprecated' for field status"

async def test_update_permission_with_description(authorized_client_rbac_manager):
    payload = test_payload.copy()
    payload["description"] = "Test Description"
    response = await authorized_client_rbac_manager.patch("/authorization/permissions/permission_update", json=payload)
    assert response.json()["description"] == payload["description"]

async def test_update_permission_with_permission_code(authorized_client_rbac_manager):
    payload = test_payload.copy()
    payload["permission_code"] = "test_permission_update"
    response = await authorized_client_rbac_manager.patch("/authorization/permissions/permission_update", json=payload)
    assert response.status_code == 200 
    # permission_code should not be updated
    assert response.json()["permission_code"] == "PERMISSION_UPDATE"

async def test_update_permission_with_system_permission(authorized_client_rbac_manager):
    new_permission = await authorized_client_rbac_manager.post("/authorization/permissions", json={
        "permission_code": "test_permission_update",
        "permission_name": "Test Permission Update",
        "module": "permission",
        "category": "update",
        "is_system_permission": "true"
    })
    assert new_permission.status_code == 201
    assert new_permission.json()["permission_code"] == "TEST_PERMISSION_UPDATE"
    assert new_permission.json()["is_system_permission"] is True
    response = await authorized_client_rbac_manager.patch("/authorization/permissions/test_permission_update", json=test_payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot update a system permission"