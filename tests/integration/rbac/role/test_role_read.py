import pytest

pytestmark = pytest.mark.asyncio

# Get all roles
async def test_superadmin_get_all_roles(authorized_client_superadmin):
    response = await authorized_client_superadmin.get("/authorization/roles")
    assert response.status_code == 200
    assert response.json() is not None
    assert len(response.json()) == 1 # initial seeded role from app.db.seed.roles.py

async def test_user_no_permission_get_all_roles(authorized_client_human_no_role):
    response = await authorized_client_human_no_role.get("/authorization/roles")
    assert response.status_code == 403
    assert response.json()["detail"] == "User does not have permission to access ROLE_VIEW"

async def test_rbac_manager_get_all_roles(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.get("/authorization/roles")
    assert response.status_code == 200
    assert response.json() is not None
    assert len(response.json()) == 2 # initial seeded role from app.db.seed.roles.py + conftest fixture RBAC_MANAGER role

async def test_get_all_roles_with_deleted_status(authorized_client_rbac_manager, authorized_client_superadmin):
    response = await authorized_client_superadmin.delete("/authorization/roles/rbac_manager")
    assert response.status_code == 204

    response = await authorized_client_superadmin.get("/authorization/roles")
    assert response.status_code == 200
    assert response.json() is not None
    assert len(response.json()) == 1

    response = await authorized_client_superadmin.get("/authorization/roles?include_deleted=true")
    assert response.status_code == 200
    assert response.json() is not None
    assert len(response.json()) == 2

# Get role by code
async def test_superadmin_get_role_by_code(authorized_client_superadmin):
    response = await authorized_client_superadmin.get("/authorization/roles/superadmin")
    assert response.status_code == 200
    assert response.json() is not None
    assert response.json()["role_code"] == "SUPERADMIN"

async def test_user_no_permission_get_role_by_code(authorized_client_human_no_role):
    response = await authorized_client_human_no_role.get("/authorization/roles/superadmin")
    assert response.status_code == 403
    assert response.json()["detail"] == "User does not have permission to access ROLE_VIEW"

async def test_rbac_manager_get_role_by_code(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.get("/authorization/roles/rbac_manager")
    assert response.status_code == 200
    assert response.json() is not None
    assert response.json()["role_code"] == "RBAC_MANAGER"

async def test_get_role_by_code_for_deleted_role(authorized_client_rbac_manager, authorized_client_superadmin):
    response = await authorized_client_superadmin.delete("/authorization/roles/rbac_manager")
    assert response.status_code == 204
    response = await authorized_client_superadmin.get("/authorization/roles/rbac_manager")
    assert response.status_code == 404
    assert response.json()["detail"] == "Role with code RBAC_MANAGER not found"

async def test_get_role_by_code_for_nonexistent_role(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.get("/authorization/roles/nonexistent")
    assert response.status_code == 404
    assert response.json()["detail"] == "Role with code NONEXISTENT not found"
