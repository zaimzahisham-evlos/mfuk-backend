import pytest

pytestmark = pytest.mark.asyncio

async def test_superadmin_delete_role(authorized_client_rbac_manager, authorized_client_superadmin):
    response = await authorized_client_superadmin.delete("/authorization/roles/rbac_manager")
    assert response.status_code == 204

async def test_user_no_permission_delete_role(authorized_client_human_no_role):
    response = await authorized_client_human_no_role.delete("/authorization/roles/superadmin")
    assert response.status_code == 403
    assert response.json()["detail"] == "User does not have permission to access ROLE_DELETE"

async def test_rbac_manager_delete_role(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.post("/authorization/roles", json={
        "role_code": "test_role",
        "role_name": "Test Role",
    })
    response = await authorized_client_rbac_manager.delete("/authorization/roles/test_role")
    assert response.status_code == 204
    response = await authorized_client_rbac_manager.delete("/authorization/roles/test_role")
    assert response.status_code == 404
    assert response.json()["detail"] == "Role with code TEST_ROLE not found"

async def test_delete_role_with_nonexistent_role_code(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.delete("/authorization/roles/nonexistent")
    assert response.status_code == 404
    assert response.json()["detail"] == "Role with code NONEXISTENT not found"

async def test_delete_role_with_system_role(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.delete("/authorization/roles/superadmin")
    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot delete a system role"