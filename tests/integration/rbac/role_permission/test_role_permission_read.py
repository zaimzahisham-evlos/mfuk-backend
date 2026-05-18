import pytest

pytestmark = pytest.mark.asyncio

async def test_superadmin_get_role_permissions(authorized_client_superadmin, authorized_client_rbac_manager):
    role = await authorized_client_superadmin.get("/authorization/roles/rbac_manager")
    role_id = role.json()["id"]
    response = await authorized_client_superadmin.get(f"/authorization/roles/{role_id}/permissions")
    assert response.status_code == 200
    assert len(response.json()) == 50 # 50 permissions assigned to the role on fixture setup

async def test_rbac_manager_get_role_permissions(authorized_client_rbac_manager):
    role = await authorized_client_rbac_manager.get("/authorization/roles/rbac_manager")
    role_id = role.json()["id"]
    response = await authorized_client_rbac_manager.get(f"/authorization/roles/{role_id}/permissions")
    assert response.status_code == 200
    assert len(response.json()) == 50 # 50 permissions assigned to the role on fixture setup

async def test_get_role_permissions_with_nonexistent_role_id(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.get("/authorization/roles/999999/permissions")
    assert response.status_code == 404
    assert response.json()["detail"] == "Role with ID 999999 not found"

async def test_get_role_permissions_with_statuses(authorized_client_rbac_manager):
    role = await authorized_client_rbac_manager.get("/authorization/roles/rbac_manager")
    role_id = role.json()["id"]
    response = await authorized_client_rbac_manager.get(f"/authorization/roles/{role_id}/permissions", params={"statuses": ["Inactive"]})
    assert response.status_code == 200
    assert len(response.json()) == 5 # override permissions are inactive on 5 modules on fixture setup

async def test_get_role_permissions_with_invalid_statuses(authorized_client_rbac_manager):
    role = await authorized_client_rbac_manager.get("/authorization/roles/rbac_manager")
    role_id = role.json()["id"]
    response = await authorized_client_rbac_manager.get(f"/authorization/roles/{role_id}/permissions", params={"statuses": ["Invalid", "Active"]})
    assert response.status_code == 422
    assert response.json()["detail"] == "Input should be 'Active', 'Inactive', 'Deleted' or 'Suspended' for field statuses"

async def test_get_role_permissions_include_deleted(authorized_client_rbac_manager):
    role = await authorized_client_rbac_manager.get("/authorization/roles/rbac_manager")
    role_id = role.json()["id"]
    response = await authorized_client_rbac_manager.get(f"/authorization/roles/{role_id}/permissions", params={"statuses": ["Inactive"]})
    role_permission_id = response.json()[0]["id"]
    response = await authorized_client_rbac_manager.delete(f"/authorization/role-permission/{role_permission_id}")
    assert response.status_code == 204
    response = await authorized_client_rbac_manager.get(f"/authorization/roles/{role_id}/permissions", params={"statuses": ["Inactive"]})
    assert response.status_code == 200
    assert len(response.json()) == 4 # 4 override permissions are inactive on 4 modules on fixture setup
    response = await authorized_client_rbac_manager.get(f"/authorization/roles/{role_id}/permissions", params={"statuses": ["Inactive"], "include_deleted": "true"})
    assert response.status_code == 200
    assert len(response.json()) == 5 # 5 permissions are inactive on 5 modules on fixture setup

async def test_get_role_permission(authorized_client_rbac_manager):
    role = await authorized_client_rbac_manager.get("/authorization/roles/rbac_manager")
    role_id = role.json()["id"]
    response = await authorized_client_rbac_manager.get(f"/authorization/roles/{role_id}/permissions")
    role_permission_id = response.json()[0]["id"]
    response = await authorized_client_rbac_manager.get(f"/authorization/role-permission/{role_permission_id}")
    assert response.status_code == 200
    assert response.json()["id"] == role_permission_id
    assert response.json()["role_id"] == role_id

async def test_get_role_permission_with_nonexistent_role_permission_id(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.get("/authorization/role-permission/999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Role permission with ID 999999 not found"

