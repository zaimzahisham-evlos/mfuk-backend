import pytest

pytestmark = pytest.mark.asyncio

async def test_superadmin_delete_permission(authorized_client_superadmin):
    response = await authorized_client_superadmin.delete("/authorization/permissions/permission_update")
    assert response.status_code == 204

async def test_user_no_permission_delete_permission(authorized_client_human_no_role):
    response = await authorized_client_human_no_role.delete("/authorization/permissions/permission_update")
    assert response.status_code == 403
    assert response.json()["detail"] == "User does not have permission to access PERMISSION_DELETE"

async def test_rbac_manager_delete_permission(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.delete("/authorization/permissions/permission_update")
    assert response.status_code == 204
    response = await authorized_client_rbac_manager.delete("/authorization/permissions/permission_update")
    assert response.status_code == 404
    assert response.json()["detail"] == "Permission with code PERMISSION_UPDATE not found"

async def test_delete_permission_with_nonexistent_permission_code(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.delete("/authorization/permissions/nonexistent")
    assert response.status_code == 404
    assert response.json()["detail"] == "Permission with code NONEXISTENT not found"

async def test_delete_permission_with_system_permission(authorized_client_rbac_manager):
    new_permission = await authorized_client_rbac_manager.post("/authorization/permissions", json={
        "permission_code": "test_permission_delete",
        "permission_name": "Test Permission Delete",
        "module": "permission",
        "category": "delete",
        "is_system_permission": "true"
    })
    assert new_permission.status_code == 201
    assert new_permission.json()["permission_code"] == "TEST_PERMISSION_DELETE"
    assert new_permission.json()["is_system_permission"] is True
    response = await authorized_client_rbac_manager.delete("/authorization/permissions/test_permission_delete")
    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot delete a system permission"