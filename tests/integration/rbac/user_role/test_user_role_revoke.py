import pytest

pytestmark = pytest.mark.integration

async def test_superadmin_revoke_roles_from_user(authorized_client_rbac_manager, authorized_client_superadmin):
    response = await authorized_client_superadmin.get("/users/rbacmanager")
    user = response.json()
    user_roles = await authorized_client_superadmin.get(f"authorization/users/{user['id']}/roles")
    assert len(user_roles.json()) == 1
    user_role = user_roles.json()[0]
    response = await authorized_client_superadmin.patch(f"authorization/users/{user['id']}/roles/revoke", json={
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
    user_roles = await authorized_client_superadmin.get(f"authorization/users/{user['id']}/roles")
    assert len(user_roles.json()) == 1
    assert user_roles.json()[0]["status"] == "Revoked"
    assert user_roles.json()[0]["revoked_at"] is not None
    assert user_roles.json()[0]["revoked_by_id"] is not None
    assert user_roles.json()[0]["updated_at"] is not None
    assert user_roles.json()[0]["updated_by_id"] is not None

async def test_rbac_manager_revoke_roles_from_user(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.get("/users/superadmin")
    user = response.json()
    user_roles = await authorized_client_rbac_manager.get(f"authorization/users/{user['id']}/roles")
    assert len(user_roles.json()) == 1
    user_role = user_roles.json()[0]
    response = await authorized_client_rbac_manager.patch(f"authorization/users/{user['id']}/roles/revoke", json={
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
    user_roles = await authorized_client_rbac_manager.get(f"authorization/users/{user['id']}/roles")
    assert len(user_roles.json()) == 1
    assert user_roles.json()[0]["status"] == "Revoked"

async def test_user_revoke_roles_from_self(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.get("/users/rbacmanager")
    user = response.json()
    user_roles = await authorized_client_rbac_manager.get(f"authorization/users/{user['id']}/roles")
    assert len(user_roles.json()) == 1
    user_role = user_roles.json()[0]
    response = await authorized_client_rbac_manager.patch(f"authorization/users/{user['id']}/roles/revoke", json={
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
    response = await authorized_client_rbac_manager.get(f"authorization/users/{user['id']}/roles")
    assert response.status_code == 403

async def test_revoke_roles_from_user_duplicate_in_payload(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.get("/users/superadmin")
    user = response.json()
    user_roles = await authorized_client_rbac_manager.get(f"authorization/users/{user['id']}/roles")
    assert len(user_roles.json()) == 1
    user_role = user_roles.json()[0]
    response = await authorized_client_rbac_manager.patch(f"authorization/users/{user['id']}/roles/revoke", json={
        "user_roles": [
            {
                "user_role_id": user_role["id"],
            }
        ] * 2
    })
    assert response.status_code == 200
    assert response.json()["user_id"] == user['id']
    assert len(response.json()["outcomes"]) == 2
    assert response.json()["outcomes"][0]["status"] == "duplicate_entry"
    assert response.json()["outcomes"][1]["user_role_id"] == user_role["id"]
    assert response.json()["outcomes"][1]["status"] == "revoked"
    user_roles = await authorized_client_rbac_manager.get(f"authorization/users/{user['id']}/roles")
    assert len(user_roles.json()) == 1
    assert user_roles.json()[0]["status"] == "Revoked"


async def test_revoke_roles_from_user_not_found(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.patch(f"authorization/users/1/roles/revoke", json={
        "user_roles": [
            {
                "user_role_id": 999999,
            }
        ]
    })
    assert response.status_code == 404
    assert response.json()["detail"] == "User with ID 1 not found"

async def test_revoke_roles_from_user_not_found_user_role(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.get("/users/rbacmanager")
    user = response.json()
    response = await authorized_client_rbac_manager.patch(f"authorization/users/{user['id']}/roles/revoke", json={
        "user_roles": [
            {
                "user_role_id": 999999,
            }
        ]
    })
    assert response.status_code == 200
    assert response.json()["user_id"] == user['id']
    assert len(response.json()["outcomes"]) == 1
    assert response.json()["outcomes"][0]["status"] == "not_found_user_role"
    assert response.json()["outcomes"][0]["message"] == "User role with ID 999999 not found"
    user_roles = await authorized_client_rbac_manager.get(f"authorization/users/{user['id']}/roles")
    assert len(user_roles.json()) == 1
    assert user_roles.json()[0]["status"] == "Active"

async def test_revoke_roles_from_user_already_revoked(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.get("/users/superadmin")
    user = response.json()
    user_roles = await authorized_client_rbac_manager.get(f"authorization/users/{user['id']}/roles")
    assert len(user_roles.json()) == 1
    user_role = user_roles.json()[0]
    response = await authorized_client_rbac_manager.patch(f"authorization/users/{user['id']}/roles/revoke", json={
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
    user_roles = await authorized_client_rbac_manager.get(f"authorization/users/{user['id']}/roles")
    assert len(user_roles.json()) == 1
    assert user_roles.json()[0]["status"] == "Revoked"

    response = await authorized_client_rbac_manager.patch(f"authorization/users/{user['id']}/roles/revoke", json={
        "user_roles": [
            {
                "user_role_id": user_role["id"],
            }
        ]
    })
    assert response.status_code == 200
    assert response.json()["user_id"] == user['id']
    assert len(response.json()["outcomes"]) == 1
    assert response.json()["outcomes"][0]["status"] == "already_revoked"
    assert response.json()["outcomes"][0]["message"] == f"User role with ID {user_role['id']} already revoked"