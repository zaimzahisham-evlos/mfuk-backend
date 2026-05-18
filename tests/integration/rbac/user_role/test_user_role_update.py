import pytest

pytestmark = pytest.mark.integration

async def test_superadmin_update_user_role(authorized_client_rbac_manager, authorized_client_superadmin):
    response = await authorized_client_superadmin.get("/users/rbacmanager")
    user = response.json()
    user_roles = await authorized_client_superadmin.get(f"authorization/users/{user['id']}/roles")
    assert len(user_roles.json()) == 1
    user_role = user_roles.json()[0]
    response = await authorized_client_superadmin.patch(f"authorization/user-role/{user_role['id']}", json={
        "status": "Inactive",
    })
    assert response.status_code == 200
    assert response.json()["status"] == "Inactive"
    user_roles = await authorized_client_superadmin.get(f"authorization/users/{user['id']}/roles")
    assert response.status_code == 200
    assert response.json()["status"] == "Inactive"
    assert response.json()["updated_at"] is not None
    assert response.json()["updated_by_id"] is not None

async def test_rbac_manager_update_user_role(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.get("/users/superadmin")
    user = response.json()
    user_roles = await authorized_client_rbac_manager.get(f"authorization/users/{user['id']}/roles")
    assert len(user_roles.json()) == 1
    user_role = user_roles.json()[0]
    response = await authorized_client_rbac_manager.patch(f"authorization/user-role/{user_role['id']}", json={
        "status": "Inactive",
    })
    assert response.status_code == 200
    assert response.json()["status"] == "Inactive"
    assert response.json()["updated_at"] is not None
    assert response.json()["updated_by_id"] is not None
    user_roles = await authorized_client_rbac_manager.get(f"authorization/users/{user['id']}/roles")
    assert len(user_roles.json()) == 1
    assert user_roles.json()[0]["status"] == "Inactive"
    assert user_roles.json()[0]["updated_at"] is not None
    assert user_roles.json()[0]["updated_by_id"] is not None

async def test_user_update_user_role_self(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.get("/users/rbacmanager")
    user = response.json()
    user_roles = await authorized_client_rbac_manager.get(f"authorization/users/{user['id']}/roles")
    assert len(user_roles.json()) == 1
    user_role = user_roles.json()[0]
    response = await authorized_client_rbac_manager.patch(f"authorization/user-role/{user_role['id']}", json={
        "status": "Inactive",
    })
    assert response.status_code == 200
    assert response.json()["status"] == "Inactive"
    assert response.json()["updated_at"] is not None
    assert response.json()["updated_by_id"] is not None
    response = await authorized_client_rbac_manager.get(f"authorization/users/{user['id']}/roles")
    assert response.status_code == 403

async def test_update_user_role_with_invalid_status(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.get("/users/rbacmanager")
    user = response.json()
    user_roles = await authorized_client_rbac_manager.get(f"authorization/users/{user['id']}/roles")
    assert len(user_roles.json()) == 1
    user_role = user_roles.json()[0]
    response = await authorized_client_rbac_manager.patch(f"authorization/user-role/{user_role['id']}", json={
        "status": "Invalid",
    })
    assert response.status_code == 422
    assert response.json()["detail"] == "Input should be 'Active', 'Inactive', 'Deleted', 'Suspended' or 'Revoked' for field status"

async def test_update_user_role_with_status_deleted(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.get("/users/rbacmanager")
    user = response.json()
    user_roles = await authorized_client_rbac_manager.get(f"authorization/users/{user['id']}/roles")
    assert len(user_roles.json()) == 1
    user_role = user_roles.json()[0]
    response = await authorized_client_rbac_manager.patch(f"authorization/user-role/{user_role['id']}", json={
        "status": "Deleted",
    })
    assert response.status_code == 422
    assert response.json()["detail"] == "Value error, Use delete user role endpoint to delete a user role"

async def test_update_user_role_with_status_revoked(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.get("/users/rbacmanager")
    user = response.json()
    user_roles = await authorized_client_rbac_manager.get(f"authorization/users/{user['id']}/roles")
    assert len(user_roles.json()) == 1
    user_role = user_roles.json()[0]
    response = await authorized_client_rbac_manager.patch(f"authorization/user-role/{user_role['id']}", json={
        "status": "Revoked",
    })
    assert response.status_code == 422
    assert response.json()["detail"] == "Value error, Use revoke user role endpoint to revoke a user role"

async def test_update_deleted_user_role(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.get("/users/superadmin")
    user = response.json()
    user_roles = await authorized_client_rbac_manager.get(f"authorization/users/{user['id']}/roles")
    assert len(user_roles.json()) == 1
    user_role = user_roles.json()[0]
    response = await authorized_client_rbac_manager.delete(f"authorization/user-role/{user_role['id']}")
    assert response.status_code == 204
    response = await authorized_client_rbac_manager.patch(f"authorization/user-role/{user_role['id']}", json={
        "status": "Inactive",
    })
    assert response.status_code == 404
    assert response.json()["detail"] == f"User role with ID {user_role['id']} not found"

async def test_update_revoked_user_role(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.get("/users/superadmin")
    user = response.json()
    user_roles = await authorized_client_rbac_manager.get(f"authorization/users/{user['id']}/roles")
    assert len(user_roles.json()) == 1
    user_role = user_roles.json()[0]
    response = await authorized_client_rbac_manager.patch(f"authorization/users/{user["id"]}/roles/revoke", json={
        "user_roles": [
            {
                "user_role_id": user_role["id"],
            }
        ]
    })
    assert response.status_code == 200
    assert response.json()["user_id"] == user['id']
    assert len(response.json()["outcomes"]) == 1
    assert response.json()["outcomes"][0]["status"] == "revoked"
    response = await authorized_client_rbac_manager.patch(f"authorization/user-role/{user_role['id']}", json={
        "status": "Inactive",
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Revoked user roles cannot be updated"