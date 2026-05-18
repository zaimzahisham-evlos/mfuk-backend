import pytest

pytestmark = pytest.mark.asyncio

async def test_superadmin_delete_role_permission(authorized_client_rbac_manager, authorized_client_superadmin):
    role = await authorized_client_superadmin.get("/authorization/roles/rbac_manager")
    role_id = role.json()["id"]
    role_permissions = await authorized_client_superadmin.get(f"/authorization/roles/{role_id}/permissions")
    role_permissions = role_permissions.json()
    role_permission_id = role_permissions[0]["id"]
    response = await authorized_client_superadmin.delete(f"/authorization/role-permission/{role_permission_id}")
    assert response.status_code == 204
    response = await authorized_client_superadmin.delete(f"/authorization/role-permission/{role_permission_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == f"Role permission with ID {role_permission_id} not found"

async def test_rbac_manager_delete_role_permission(authorized_client_rbac_manager):
    role = await authorized_client_rbac_manager.get("/authorization/roles/rbac_manager")
    role_id = role.json()["id"]
    role_permissions = await authorized_client_rbac_manager.get(f"/authorization/roles/{role_id}/permissions")
    role_permissions = role_permissions.json()
    role_permission_id = role_permissions[0]["id"]
    response = await authorized_client_rbac_manager.delete(f"/authorization/role-permission/{role_permission_id}")
    assert response.status_code == 204
    response = await authorized_client_rbac_manager.delete(f"/authorization/role-permission/{role_permission_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == f"Role permission with ID {role_permission_id} not found"

async def test_delete_role_permission_not_found(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.delete("/authorization/role-permission/999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Role permission with ID 999999 not found"

async def test_user_no_permission_delete_role_permission(authorized_client_human_no_role):
    response = await authorized_client_human_no_role.delete("/authorization/role-permission/1")
    assert response.status_code == 403
    assert response.json()["detail"] == "User does not have permission to access ROLE_PERMISSION_DELETE"
