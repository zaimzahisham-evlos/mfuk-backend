import pytest

pytestmark = pytest.mark.asyncio

test_payload = {
    "role_name": "Test Role Update",
}

def assert_role_updated(response, payload):
    assert response.status_code == 200
    assert response.json()["role_name"] == payload["role_name"]
    assert response.json()["auth_required"] is True
    assert response.json()["is_system_role"] is False
    assert response.json()["status"] == "Active"
    assert response.json()["description"] is None
    assert response.json()["updated_at"] is not None

async def test_superadmin_update_role(authorized_client_rbac_manager, authorized_client_superadmin):
    response = await authorized_client_superadmin.patch("/authorization/roles/rbac_manager", json=test_payload)
    assert_role_updated(response, test_payload)

async def test_user_no_permission_update_role(authorized_client_human_no_role):
    response = await authorized_client_human_no_role.patch("/authorization/roles/test_role", json=test_payload)
    assert response.status_code == 403
    assert response.json()["detail"] == "User does not have permission to access ROLE_UPDATE"

async def test_rbac_manager_update_role(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.patch("/authorization/roles/rbac_manager", json=test_payload)
    assert_role_updated(response, test_payload)

async def test_update_role_with_blank_role_name(authorized_client_rbac_manager):
    payload = test_payload.copy()
    payload["role_name"] = " "
    response = await authorized_client_rbac_manager.patch("/authorization/roles/rbac_manager", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"] == "Value error, Value cannot be blank for field role_name"

async def test_update_role_with_deleted_status(authorized_client_rbac_manager):
    payload = test_payload.copy()
    payload["status"] = "Deleted"
    response = await authorized_client_rbac_manager.patch("/authorization/roles/rbac_manager", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "Deleted"
    assert response.json()["deleted_at"] is not None
    assert response.json()["deleted_by_id"] is not None

async def test_update_role_with_invalid_status(authorized_client_rbac_manager):
    payload = test_payload.copy()
    payload["status"] = "Invalid"
    response = await authorized_client_rbac_manager.patch("/authorization/roles/rbac_manager", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"] == "Input should be 'Active', 'Inactive', 'Deleted' or 'Suspended' for field status"

async def test_update_role_with_description(authorized_client_rbac_manager):
    payload = test_payload.copy()
    payload["description"] = "Test Description"
    response = await authorized_client_rbac_manager.patch("/authorization/roles/rbac_manager", json=payload)
    assert response.status_code == 200
    assert response.json()["description"] == payload["description"]

async def test_update_role_with_role_code(authorized_client_rbac_manager):
    payload = test_payload.copy()
    payload["role_code"] = "test_role"
    response = await authorized_client_rbac_manager.patch("/authorization/roles/rbac_manager", json=payload)
    assert response.status_code == 200
    assert response.json()["role_code"] == "RBAC_MANAGER" # role_code is immutable

async def test_update_role_with_auth_required(authorized_client_rbac_manager):
    payload = test_payload.copy()
    payload["auth_required"] = "false"
    response = await authorized_client_rbac_manager.patch("/authorization/roles/rbac_manager", json=payload)
    assert response.status_code == 200
    assert response.json()["auth_required"] is False

async def test_update_role_with_system_role(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.patch("/authorization/roles/superadmin", json=test_payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot update a system role"
