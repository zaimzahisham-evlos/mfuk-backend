import pytest

pytestmark = pytest.mark.asyncio

test_payload = {
    "permission_code": "test_permission_create",
    "permission_name": "Test Permission Create",
    "module": "permission",
    "category": "create"
}

def assert_permission_created(response, payload):
    assert response.status_code == 201
    assert response.json()["permission_code"] == payload["permission_code"].upper()
    assert response.json()["permission_name"] == payload["permission_name"].title()
    assert response.json()["module"] == payload["module"].title()
    assert response.json()["category"] == payload["category"]
    assert response.json()["status"] == "Active"
    assert response.json()["description"] is None
    assert response.json()["is_system_permission"] is False
    assert response.json()["created_by_id"] is not None
    assert response.json()["created_at"] is not None
    assert response.json()["updated_at"] is None
    assert response.json()["deleted_at"] is None
    assert response.json()["deleted_by_id"] is None


async def test_superadmin_create_permission(authorized_client_superadmin):
    response = await authorized_client_superadmin.post("/authorization/permissions", json=test_payload)
    assert_permission_created(response, test_payload)

async def test_user_no_permission_create_permission(authorized_client_human_no_role):
    response = await authorized_client_human_no_role.post("/authorization/permissions", json=test_payload)
    assert response.status_code == 403
    assert response.json()["detail"] == "User does not have permission to access PERMISSION_CREATE"

async def test_rbac_manager_create_permission(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.post("/authorization/permissions", json=test_payload)
    assert_permission_created(response, test_payload)

async def test_create_permission_duplicate_permission_code(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.post("/authorization/permissions", json={
        # existing permission code that is seeded initially
        "permission_code": "permission_view",
        "permission_name": "Permission View",
        "module": "permission",
        "category": "view"
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Permission with code PERMISSION_VIEW already exists"

async def test_create_permission_duplicate_code_different_status(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.post("/authorization/permissions", json={
        "permission_code": "permission_view",
        "permission_name": "Permission View",
        "module": "permission",
        "category": "view",
        "status": "Inactive"
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Permission with code PERMISSION_VIEW already exists"
    
async def test_create_permission_with_blank_permission_code(authorized_client_rbac_manager):
    payload = test_payload.copy()
    payload["permission_code"] = " "
    response = await authorized_client_rbac_manager.post("/authorization/permissions", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"] == "Value error, Value cannot be blank for field permission_code"

async def test_create_permission_with_blank_permission_name(authorized_client_rbac_manager):
    payload = test_payload.copy()
    payload["permission_name"] = " "
    response = await authorized_client_rbac_manager.post("/authorization/permissions", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"] == "Value error, Value cannot be blank for field permission_name"

async def test_create_permission_with_blank_module(authorized_client_rbac_manager):
    payload = test_payload.copy()
    payload["module"] = " "
    response = await authorized_client_rbac_manager.post("/authorization/permissions", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"] == "Value error, Value cannot be blank for field module"

async def test_create_permission_with_blank_category(authorized_client_rbac_manager):
    payload = test_payload.copy()
    payload["category"] = " "
    response = await authorized_client_rbac_manager.post("/authorization/permissions", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"] == "Input should be 'view', 'create', 'update', 'delete', 'approve', 'export', 'assign', 'revoke', 'execute' or 'override' for field category"

async def test_create_permission_with_invalid_category(authorized_client_rbac_manager):
    payload = test_payload.copy()
    payload["category"] = "invalid"
    response = await authorized_client_rbac_manager.post("/authorization/permissions", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"] == "Input should be 'view', 'create', 'update', 'delete', 'approve', 'export', 'assign', 'revoke', 'execute' or 'override' for field category"

async def test_create_permission_with_deleted_status(authorized_client_rbac_manager):
    payload = test_payload.copy()
    payload["status"] = "Deleted"
    response = await authorized_client_rbac_manager.post("/authorization/permissions", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot create a permission with status Deleted"

async def test_create_permission_with_invalid_status(authorized_client_rbac_manager):
    payload = test_payload.copy()
    payload["status"] = "invalid"
    response = await authorized_client_rbac_manager.post("/authorization/permissions", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"] == "Input should be 'Active', 'Inactive', 'Deleted' or 'Deprecated' for field status"

async def test_create_permission_with_description(authorized_client_rbac_manager):
    payload = test_payload.copy()
    payload["description"] = "Test Description"
    response = await authorized_client_rbac_manager.post("/authorization/permissions", json=payload)
    assert response.json()["description"] == payload["description"]

async def test_create_permission_with_is_system_permission(authorized_client_rbac_manager):
    payload = test_payload.copy()
    payload["is_system_permission"] = "true"
    response = await authorized_client_rbac_manager.post("/authorization/permissions", json=payload)
    assert response.json()["is_system_permission"] is True

async def test_create_permission_with_invalid_permission_code(authorized_client_rbac_manager):
    payload = test_payload.copy()
    payload["permission_code"] = "test-permission"
    response = await authorized_client_rbac_manager.post("/authorization/permissions", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"] == "String should match pattern '^[A-Z0-9_]+$' for field permission_code"

async def test_create_permission_with_short_permission_code(authorized_client_rbac_manager):
    payload = test_payload.copy()
    payload["permission_code"] = "t"
    response = await authorized_client_rbac_manager.post("/authorization/permissions", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"] == "String should have at least 3 characters for field permission_code"

async def test_create_permission_with_long_permission_code(authorized_client_rbac_manager):
    payload = test_payload.copy()
    payload["permission_code"] = "test"*30
    response = await authorized_client_rbac_manager.post("/authorization/permissions", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"] == "String should have at most 80 characters for field permission_code"

