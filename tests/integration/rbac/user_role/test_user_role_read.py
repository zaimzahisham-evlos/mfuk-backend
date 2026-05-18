import pytest

pytestmark = pytest.mark.integration

async def test_superadmin_get_user_roles(authorized_client_rbac_manager, authorized_client_superadmin):
    response = await authorized_client_superadmin.get("/users/rbacmanager")
    user = response.json()
    response = await authorized_client_superadmin.get(f"authorization/users/{user['id']}/roles")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]['user_id'] == user['id']
    assert response.json()[0]['role_id'] == user["role_codes"][0]['id']

async def test_rbac_manager_get_user_roles(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.get("/users/rbacmanager")
    user = response.json()
    response = await authorized_client_rbac_manager.get(f"authorization/users/{user['id']}/roles")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]['user_id'] == user['id']
    assert response.json()[0]['role_id'] == user["role_codes"][0]['id']

async def test_get_user_roles_with_nonexistent_user_id(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.get("/authorization/users/999999/roles")
    assert response.status_code == 404
    assert response.json()["detail"] == "User with ID 999999 not found"

async def test_get_user_roles_with_statuses(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.get("/users/rbacmanager")
    user = response.json()
    response = await authorized_client_rbac_manager.get(f"authorization/users/{user['id']}/roles", params={"statuses": ["Inactive"]})
    assert response.status_code == 200
    assert len(response.json()) == 0

async def test_get_user_roles_include_deleted(authorized_client_user_manager, authorized_client_rbac_manager):
    user = await authorized_client_rbac_manager.get("/users/usermanager")
    user = user.json()
    user_roles = await authorized_client_rbac_manager.get(f"authorization/users/{user['id']}/roles")
    user_role_id = user_roles.json()[0]['id']
    response = await authorized_client_rbac_manager.delete(f"authorization/user-role/{user_role_id}")
    assert response.status_code == 204
    response = await authorized_client_rbac_manager.get(f"authorization/users/{user['id']}/roles")
    assert response.status_code == 200
    assert len(response.json()) == 0
    response = await authorized_client_rbac_manager.get(f"authorization/users/{user['id']}/roles?include_deleted=true")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]['status'] == "Deleted"

async def test_get_user_roles_invalid_statuses(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.get("/users/rbacmanager")
    user = response.json()
    response = await authorized_client_rbac_manager.get(f"authorization/users/{user['id']}/roles", params={"statuses": ["Invalid"]})
    assert response.status_code == 422
    assert response.json()["detail"] == "Input should be 'Active', 'Inactive', 'Deleted', 'Suspended' or 'Revoked' for field statuses"

async def test_get_user_role(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.get("/users/rbacmanager")
    user = response.json()
    response = await authorized_client_rbac_manager.get(f"authorization/users/{user['id']}/roles")
    user_role_id = response.json()[0]['id']
    response = await authorized_client_rbac_manager.get(f"authorization/user-role/{user_role_id}")
    assert response.status_code == 200
    assert response.json()['id'] == user_role_id
    assert response.json()['user_id'] == user['id']
    assert response.json()['role_id'] == user["role_codes"][0]['id']

async def test_get_user_role_with_nonexistent_user_role_id(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.get("/authorization/user-role/999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "User role with ID 999999 not found"