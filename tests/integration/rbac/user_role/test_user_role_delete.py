import pytest

pytestmark = pytest.mark.integration

async def test_superadmin_delete_user_role(authorized_client_rbac_manager, authorized_client_superadmin):
    response = await authorized_client_superadmin.get("/users/rbacmanager")
    user = response.json()
    user_roles = await authorized_client_superadmin.get(f"authorization/users/{user['id']}/roles")
    assert len(user_roles.json()) == 1
    user_role = user_roles.json()[0]
    response = await authorized_client_superadmin.delete(f"authorization/user-role/{user_role['id']}")
    assert response.status_code == 204
    user_roles = await authorized_client_superadmin.get(f"authorization/users/{user['id']}/roles")
    assert len(user_roles.json()) == 0
    response = await authorized_client_superadmin.delete(f"authorization/user-role/{user_role['id']}")
    assert response.status_code == 404
    assert response.json()["detail"] == f"User role with ID {user_role['id']} not found"

async def test_rbac_manager_delete_user_role(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.get("/users/superadmin")
    user = response.json()
    user_roles = await authorized_client_rbac_manager.get(f"authorization/users/{user['id']}/roles")
    assert len(user_roles.json()) == 1
    user_role = user_roles.json()[0]
    response = await authorized_client_rbac_manager.delete(f"authorization/user-role/{user_role['id']}")
    assert response.status_code == 204
    user_roles = await authorized_client_rbac_manager.get(f"authorization/users/{user['id']}/roles")
    assert len(user_roles.json()) == 0
    response = await authorized_client_rbac_manager.delete(f"authorization/user-role/{user_role['id']}")
    assert response.status_code == 404
    assert response.json()["detail"] == f"User role with ID {user_role['id']} not found"

async def test_user_delete_user_role_self(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.get("/users/rbacmanager")
    user = response.json()
    user_roles = await authorized_client_rbac_manager.get(f"authorization/users/{user['id']}/roles")
    assert len(user_roles.json()) == 1
    user_role = user_roles.json()[0]
    response = await authorized_client_rbac_manager.delete(f"authorization/user-role/{user_role['id']}")
    assert response.status_code == 204
    response = await authorized_client_rbac_manager.get(f"authorization/users/{user['id']}/roles")
    assert response.status_code == 403
    
async def test_delete_user_role_not_found(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.delete(f"authorization/user-role/999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "User role with ID 999999 not found"