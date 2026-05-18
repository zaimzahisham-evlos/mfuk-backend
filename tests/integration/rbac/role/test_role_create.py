import pytest

pytestmark = pytest.mark.asyncio

test_payload = {
    "role_code": "test_role",
    "role_name": "Test Role"
}

def assert_role_created(response, payload):
    assert response.status_code == 201
    assert response.json()["role_code"] == payload["role_code"].upper()
    assert response.json()["role_name"] == payload["role_name"].title()
    assert response.json()["auth_required"] is True
    assert response.json()["is_system_role"] is False
    assert response.json()["status"] == "Active"
    assert response.json()["description"] is None
    assert response.json()["created_by_id"] is not None
    assert response.json()["created_at"] is not None
    assert response.json()["updated_at"] is None
    assert response.json()["deleted_at"] is None
    assert response.json()["deleted_by_id"] is None

async def test_superadmin_create_role(authorized_client_superadmin):
    response = await authorized_client_superadmin.post("/authorization/roles", json=test_payload)
    assert_role_created(response, test_payload)

async def test_user_no_permission_create_role(authorized_client_human_no_role):
    response = await authorized_client_human_no_role.post("/authorization/roles", json=test_payload)
    assert response.status_code == 403
    assert response.json()["detail"] == "User does not have permission to access ROLE_CREATE"

async def test_rbac_manager_create_role(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.post("/authorization/roles", json=test_payload)
    assert_role_created(response, test_payload)

async def test_create_role_duplicate_role_code(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.post("/authorization/roles", json={
        # existing role code that is seeded initially at conftest fixture RBAC_MANAGER role
        "role_code": "rbac_manager",
        "role_name": "RBAC Manager"
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Role with code RBAC_MANAGER already exists"

async def test_create_role_duplicate_role_code_different_status(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.post("/authorization/roles", json={
        "role_code": "rbac_manager",
        "role_name": "RBAC Manager",
        "status": "Inactive"
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Role with code RBAC_MANAGER already exists"

async def test_create_role_with_blank_role_code(authorized_client_rbac_manager):
    payload = test_payload.copy()
    payload["role_code"] = " "
    response = await authorized_client_rbac_manager.post("/authorization/roles", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"] == "Value error, Value cannot be blank for field role_code"

async def test_create_role_with_blank_role_name(authorized_client_rbac_manager):
    payload = test_payload.copy()
    payload["role_name"] = " "
    response = await authorized_client_rbac_manager.post("/authorization/roles", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"] == "Value error, Value cannot be blank for field role_name"

async def test_create_role_with_deleted_status(authorized_client_rbac_manager):
    payload = test_payload.copy()
    payload["status"] = "Deleted"
    response = await authorized_client_rbac_manager.post("/authorization/roles", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot create a role with status Deleted"

async def test_create_role_with_invalid_status(authorized_client_rbac_manager):
    payload = test_payload.copy()
    payload["status"] = "Invalid"
    response = await authorized_client_rbac_manager.post("/authorization/roles", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"] == "Input should be 'Active', 'Inactive', 'Deleted' or 'Suspended' for field status"

async def test_create_role_with_description(authorized_client_rbac_manager):
    payload = test_payload.copy()
    payload["description"] = "Test Description"
    response = await authorized_client_rbac_manager.post("/authorization/roles", json=payload)
    assert response.status_code == 201
    assert response.json()["description"] == payload["description"]

async def test_create_role_with_is_system_role(authorized_client_rbac_manager):
    payload = test_payload.copy()
    payload["is_system_role"] = "true"
    response = await authorized_client_rbac_manager.post("/authorization/roles", json=payload)
    assert response.status_code == 201
    assert response.json()["is_system_role"] is True

async def test_create_role_with_invalid_role_code(authorized_client_rbac_manager):
    payload = test_payload.copy()
    payload["role_code"] = "invalid-code"
    response = await authorized_client_rbac_manager.post("/authorization/roles", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"] == "String should match pattern '^[A-Z0-9_]+$' for field role_code"

async def test_create_role_with_short_role_code(authorized_client_rbac_manager):
    payload = test_payload.copy()
    payload["role_code"] = "a"
    response = await authorized_client_rbac_manager.post("/authorization/roles", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"] == "String should have at least 3 characters for field role_code"

async def test_create_role_with_long_role_code(authorized_client_rbac_manager):
    payload = test_payload.copy()
    payload["role_code"] = "a" * 81
    response = await authorized_client_rbac_manager.post("/authorization/roles", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"] == "String should have at most 80 characters for field role_code"