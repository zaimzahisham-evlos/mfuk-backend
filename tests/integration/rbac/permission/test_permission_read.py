import pytest

pytestmark = pytest.mark.asyncio

# Get all permissions
async def test_superadmin_get_all_permissions(authorized_client_superadmin):
    response = await authorized_client_superadmin.get("/authorization/permissions")
    assert response.status_code == 200
    # initial seeded permissions for each module and category from app.db.seed.permissions.py
    assert len(response.json()) == 50 

async def test_user_no_permission_get_all_permissions(authorized_client_human_no_role):
    response = await authorized_client_human_no_role.get("/authorization/permissions")
    assert response.status_code == 403
    assert response.json()["detail"] == "User does not have permission to access PERMISSION_VIEW"

async def test_rbac_manager_get_all_permissions(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.get("/authorization/permissions")
    assert response.status_code == 200
    # initial seeded permissions for each module and category from app.db.seed.permissions.py
    assert len(response.json()) == 50 

async def test_get_permissions_for_modules(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.get("/authorization/permissions?modules=role&modules=permission")
    assert response.status_code == 200
    assert len(response.json()) == 20 # each module has 10 permissions

async def test_get_permissions_for_modules_with_deleted(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.delete("/authorization/permissions/permission_override")
    assert response.status_code == 204
    response = await authorized_client_rbac_manager.get("/authorization/permissions?modules=permission")
    assert response.status_code == 200
    # permission module left with 9 permissions after deleting one permission
    assert len(response.json()) == 9 
    response = await authorized_client_rbac_manager.get("/authorization/permissions?modules=permission&include_deleted=true")
    assert response.status_code == 200
    # permission module has 10 permission including the deleted one
    assert len(response.json()) == 10 

async def test_get_permissions_for_nonexistent_modules(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.get("/authorization/permissions?modules=nonexistent")
    assert response.status_code == 200
    # no permissions for nonexistent modules
    assert len(response.json()) == 0 

# Get permission by code
async def test_superadmin_get_permission_by_code(authorized_client_superadmin):
    response = await authorized_client_superadmin.get("/authorization/permissions/permission_view")
    assert response.status_code == 200
    assert response.json()["permission_code"] == "PERMISSION_VIEW"
    assert response.json()["permission_name"] == "Permission View"
    assert response.json()["module"] == "Permission"
    assert response.json()["category"] == "view"
    assert response.json()["status"] == "Active"
    assert response.json()["description"] is None

async def test_user_no_permission_get_permission_by_code(authorized_client_human_no_role):
    response = await authorized_client_human_no_role.get("/authorization/permissions/permission_view")
    assert response.status_code == 403
    assert response.json()["detail"] == "User does not have permission to access PERMISSION_VIEW"

async def test_rbac_manager_get_permission_by_code(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.get("/authorization/permissions/permission_view")
    assert response.status_code == 200
    assert response.json()["permission_code"] == "PERMISSION_VIEW"
    assert response.json()["permission_name"] == "Permission View"
    assert response.json()["module"] == "Permission"
    assert response.json()["category"] == "view"
    assert response.json()["status"] == "Active"
    assert response.json()["description"] is None

async def test_get_permission_by_code_for_deleted_permission(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.delete("/authorization/permissions/permission_override")
    assert response.status_code == 204
    response = await authorized_client_rbac_manager.get("/authorization/permissions/permission_override")
    assert response.status_code == 404
    assert response.json()["detail"] == "Permission with code PERMISSION_OVERRIDE not found"

async def test_get_permission_by_code_for_nonexistent_permission(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.get("/authorization/permissions/nonexistent")
    assert response.status_code == 404
    assert response.json()["detail"] == "Permission with code NONEXISTENT not found"

