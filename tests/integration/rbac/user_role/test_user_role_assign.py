from datetime import timedelta
import pytest

from app.core.utils import utcnow

pytestmark = pytest.mark.integration

def assert_role_to_user_assigned(outcome):
    assert outcome["status"] == "assigned"
    assert outcome["user_role"]["status"] == "Active"
    assert outcome["user_role"]["valid_from"] is None
    assert outcome["user_role"]["valid_until"] is None
    assert outcome["user_role"]["reason"] is None
    assert outcome["user_role"]["created_by_id"] is not None
    assert outcome["user_role"]["created_at"] is not None
    assert outcome["user_role"]["updated_at"] is None
    assert outcome["user_role"]["deleted_at"] is None
    assert outcome["user_role"]["deleted_by_id"] is None

async def create_and_get_new_role(authorized_client_rbac_manager):
    role = await authorized_client_rbac_manager.post("/authorization/roles", json={"role_code": "test_role", "role_name": "Test Role"})
    return role.json()

async def test_superadmin_assign_roles_to_user(authorized_client_rbac_manager, authorized_client_superadmin):
    response = await authorized_client_superadmin.get("/users/rbacmanager")
    user = response.json()
    role = await create_and_get_new_role(authorized_client_rbac_manager)
    roles_to_assign = {
        "user_roles": [
            {
                "role_id": role["id"],
            }
        ]
    }
    response = await authorized_client_superadmin.post(f"authorization/users/{user['id']}/roles", json=roles_to_assign)
    assert response.status_code == 200
    assert response.json()["user_id"] == user['id']
    assert len(response.json()["outcomes"]) == 1
    assert response.json()["outcomes"][0]["role_id"] == role["id"]
    assert_role_to_user_assigned(response.json()["outcomes"][0])
    user_roles = await authorized_client_superadmin.get(f"authorization/users/{user['id']}/roles")
    assert len(user_roles.json()) == 2

async def test_rbac_manager_assign_roles_to_user(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.get("/users/rbacmanager")
    user = response.json()
    role = await create_and_get_new_role(authorized_client_rbac_manager)
    roles_to_assign = {
        "user_roles": [
            {
                "role_id": role["id"],
            }
        ]
    }
    response = await authorized_client_rbac_manager.post(f"authorization/users/{user['id']}/roles", json=roles_to_assign)
    assert response.status_code == 200
    assert response.json()["user_id"] == user['id']
    assert len(response.json()["outcomes"]) == 1
    assert response.json()["outcomes"][0]["role_id"] == role["id"]
    assert_role_to_user_assigned(response.json()["outcomes"][0])
    user_roles = await authorized_client_rbac_manager.get(f"authorization/users/{user['id']}/roles")
    assert len(user_roles.json()) == 2

async def test_assign_roles_to_user_duplicate_in_payload(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.get("/users/rbacmanager")
    user = response.json()
    role = await create_and_get_new_role(authorized_client_rbac_manager)
    roles_to_assign = {
        "user_roles": [
            {
                "role_id": role["id"],
            }
        ] * 2
    }
    response = await authorized_client_rbac_manager.post(f"authorization/users/{user['id']}/roles", json=roles_to_assign)
    assert response.status_code == 200
    assert response.json()["user_id"] == user['id']
    assert len(response.json()["outcomes"]) == 2
    assert response.json()["outcomes"][0]["status"] == "duplicate_role"
    assert response.json()["outcomes"][1]["role_id"] == role["id"]
    assert_role_to_user_assigned(response.json()["outcomes"][1])
    user_roles = await authorized_client_rbac_manager.get(f"authorization/users/{user['id']}/roles")
    assert len(user_roles.json()) == 2

async def test_assign_roles_to_user_with_status_deleted(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.get("/users/rbacmanager")
    user = response.json()
    role = await create_and_get_new_role(authorized_client_rbac_manager)
    roles_to_assign = {
        "user_roles": [
            {
                "role_id": role["id"],
                "status": "Deleted",
            }
        ]
    }
    response = await authorized_client_rbac_manager.post(f"authorization/users/{user['id']}/roles", json=roles_to_assign)
    assert response.status_code == 422
    assert response.json()["detail"] == "Value error, Cannot assign user role with status Deleted for field user_roles"
    user_roles = await authorized_client_rbac_manager.get(f"authorization/users/{user['id']}/roles")
    assert len(user_roles.json()) == 1

async def test_assign_roles_to_user_with_status_revoked(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.get("/users/rbacmanager")
    user = response.json()
    role = await create_and_get_new_role(authorized_client_rbac_manager)
    roles_to_assign = {
        "user_roles": [
            {
                "role_id": role["id"],
                "status": "Revoked",
            }
        ]
    }
    response = await authorized_client_rbac_manager.post(f"authorization/users/{user['id']}/roles", json=roles_to_assign)
    assert response.status_code == 422
    assert response.json()["detail"] == "Value error, Cannot assign user role with status Revoked for field user_roles"
    user_roles = await authorized_client_rbac_manager.get(f"authorization/users/{user['id']}/roles")
    assert len(user_roles.json()) == 1

async def test_assign_roles_to_user_not_found_role(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.get("/users/rbacmanager")
    user = response.json()
    roles_to_assign = {
        "user_roles": [
            {
                "role_id": 999999999999999999,
            }
        ]
    }
    response = await authorized_client_rbac_manager.post(f"authorization/users/{user['id']}/roles", json=roles_to_assign)
    assert response.status_code == 200
    assert response.json()["user_id"] == user['id']
    assert len(response.json()["outcomes"]) == 1
    assert response.json()["outcomes"][0]["status"] == "not_found_role"
    assert response.json()["outcomes"][0]["message"] == "Role with ID 999999999999999999 not found"
    user_roles = await authorized_client_rbac_manager.get(f"authorization/users/{user['id']}/roles")
    assert len(user_roles.json()) == 1

async def test_assign_roles_to_not_found_user(authorized_client_rbac_manager):
    roles_to_assign = {
        "user_roles": [
            {
                "role_id": 1,
            }
        ]
    }
    response = await authorized_client_rbac_manager.post(f"authorization/users/999999999999999999/roles", json=roles_to_assign)
    assert response.status_code == 404
    assert response.json()["detail"] == "User with ID 999999999999999999 not found"

async def test_assign_roles_to_user_already_assigned(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.get("/users/rbacmanager")
    user = response.json()
    roles_to_assign = {
        "user_roles": [
            {
                "role_id": user["role_codes"][0]["id"],
            }
        ]
    }
    response = await authorized_client_rbac_manager.post(f"authorization/users/{user['id']}/roles", json=roles_to_assign)
    assert response.status_code == 200
    assert response.json()["user_id"] == user['id']
    assert len(response.json()["outcomes"]) == 1
    assert response.json()["outcomes"][0]["status"] == "already_assigned"
    assert response.json()["outcomes"][0]["message"] == f"User role with user ID {user['id']} and role ID {user['role_codes'][0]['id']} already exists with status Active"
    user_roles = await authorized_client_rbac_manager.get(f"authorization/users/{user['id']}/roles")
    assert len(user_roles.json()) == 1

async def test_assign_roles_to_user_already_assigned_different_status(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.get("/users/rbacmanager")
    user = response.json()
    role = await create_and_get_new_role(authorized_client_rbac_manager)
    roles_to_assign = {
        "user_roles": [
            {
                "role_id": role["id"],
                "status": "Inactive",
            }
        ]
    }
    response = await authorized_client_rbac_manager.post(f"authorization/users/{user['id']}/roles", json=roles_to_assign)
    assert response.status_code == 200
    assert response.json()["user_id"] == user['id']
    assert len(response.json()["outcomes"]) == 1
    assert response.json()["outcomes"][0]["status"] == "assigned"
    user_roles = await authorized_client_rbac_manager.get(f"authorization/users/{user['id']}/roles")
    assert len(user_roles.json()) == 2

    # repeat the process
    response = await authorized_client_rbac_manager.post(f"authorization/users/{user['id']}/roles", json=roles_to_assign)
    assert response.status_code == 200
    assert response.json()["user_id"] == user['id']
    assert len(response.json()["outcomes"]) == 1
    assert response.json()["outcomes"][0]["status"] == "already_assigned"
    assert response.json()["outcomes"][0]["message"] == f"User role with user ID {user['id']} and role ID {role['id']} already exists with status Inactive"
    user_roles = await authorized_client_rbac_manager.get(f"authorization/users/{user['id']}/roles")
    assert len(user_roles.json()) == 2

async def test_assign_roles_to_user_same_role_as_deleted(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.get("/users/rbacmanager")
    user = response.json()
    role = await create_and_get_new_role(authorized_client_rbac_manager)
    roles_to_assign = {
        "user_roles": [
            {
                "role_id": role["id"],
            }
        ]
    }
    response = await authorized_client_rbac_manager.post(f"authorization/users/{user['id']}/roles", json=roles_to_assign)
    assert response.status_code == 200
    assert response.json()["user_id"] == user['id']
    assert len(response.json()["outcomes"]) == 1
    assert response.json()["outcomes"][0]["status"] == "assigned"
    user_roles = await authorized_client_rbac_manager.get(f"authorization/users/{user['id']}/roles")
    assert len(user_roles.json()) == 2

    # delete the recently assigned user role
    response = await authorized_client_rbac_manager.delete(f"authorization/user-role/{user_roles.json()[1]['id']}")
    assert response.status_code == 204
    user_roles = await authorized_client_rbac_manager.get(f"authorization/users/{user['id']}/roles")
    assert len(user_roles.json()) == 1

    # reassign the role. It should be successful.
    response = await authorized_client_rbac_manager.post(f"authorization/users/{user['id']}/roles", json=roles_to_assign)
    assert response.status_code == 200
    assert response.json()["user_id"] == user['id']
    assert len(response.json()["outcomes"]) == 1
    assert response.json()["outcomes"][0]["status"] == "assigned"
    user_roles = await authorized_client_rbac_manager.get(f"authorization/users/{user['id']}/roles")
    assert len(user_roles.json()) == 2

async def test_assign_roles_to_user_same_role_as_revoked(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.get("/users/rbacmanager")
    user = response.json()
    role = await create_and_get_new_role(authorized_client_rbac_manager)
    roles_to_assign = {
        "user_roles": [
            {
                "role_id": role["id"],
            }
        ]
    }
    response = await authorized_client_rbac_manager.post(f"authorization/users/{user['id']}/roles", json=roles_to_assign)
    assert response.status_code == 200
    assert response.json()["user_id"] == user['id']
    assert len(response.json()["outcomes"]) == 1
    assert response.json()["outcomes"][0]["status"] == "assigned"
    user_roles = await authorized_client_rbac_manager.get(f"authorization/users/{user['id']}/roles")
    assert len(user_roles.json()) == 2
    
    # revoke the recently assigned user role
    response = await authorized_client_rbac_manager.patch(f"authorization/users/{user['id']}/roles/revoke", json={
        "user_roles": [
            {
                "user_role_id": user_roles.json()[1]["id"],
            }
        ]
    })
    assert response.status_code == 200
    assert response.json()["user_id"] == user['id']
    assert len(response.json()["outcomes"]) == 1
    assert response.json()["outcomes"][0]["status"] == "revoked"
    user_roles = await authorized_client_rbac_manager.get(f"authorization/users/{user['id']}/roles")
    assert len(user_roles.json()) == 2
    assert user_roles.json()[1]["status"] == "Revoked"

    # reassign the role. It should be successful.
    response = await authorized_client_rbac_manager.post(f"authorization/users/{user['id']}/roles", json=roles_to_assign)
    assert response.status_code == 200
    assert response.json()["user_id"] == user['id']
    assert len(response.json()["outcomes"]) == 1
    assert response.json()["outcomes"][0]["status"] == "assigned"
    user_roles = await authorized_client_rbac_manager.get(f"authorization/users/{user['id']}/roles")
    assert len(user_roles.json()) == 3

async def test_assign_roles_to_user_with_invalid_status(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.get("/users/rbacmanager")
    user = response.json()
    role = await create_and_get_new_role(authorized_client_rbac_manager)
    roles_to_assign = {
        "user_roles": [
            {
                "role_id": role["id"],
                "status": "Invalid",
            }
        ]
    }
    response = await authorized_client_rbac_manager.post(f"authorization/users/{user['id']}/roles", json=roles_to_assign)
    assert response.status_code == 422
    assert response.json()["detail"] == "Input should be 'Active', 'Inactive', 'Deleted', 'Suspended' or 'Revoked' for field user_roles[0].status"
    user_roles = await authorized_client_rbac_manager.get(f"authorization/users/{user['id']}/roles")
    assert len(user_roles.json()) == 1

async def test_assign_roles_to_user_with_all_fields(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.get("/users/rbacmanager")
    user = response.json()
    role = await create_and_get_new_role(authorized_client_rbac_manager)
    valid_from = utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    valid_until = (utcnow() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    roles_to_assign = {
        "user_roles": [
            {
                "role_id": role["id"],
                "status": "Active",
                "valid_from": valid_from,
                "valid_until": valid_until,
                "reason": "Test reason",
            }
        ]
    }
    response = await authorized_client_rbac_manager.post(f"authorization/users/{user['id']}/roles", json=roles_to_assign)
    assert response.status_code == 200
    assert response.json()["user_id"] == user['id']
    assert len(response.json()["outcomes"]) == 1
    assert response.json()["outcomes"][0]["status"] == "assigned"
    assert response.json()["outcomes"][0]["user_role"]["status"] == "Active"
    assert response.json()["outcomes"][0]["user_role"]["valid_from"] == valid_from
    assert response.json()["outcomes"][0]["user_role"]["valid_until"] == valid_until
    assert response.json()["outcomes"][0]["user_role"]["reason"] == "Test reason"
    user_roles = await authorized_client_rbac_manager.get(f"authorization/users/{user['id']}/roles")
    assert len(user_roles.json()) == 2

async def test_assign_roles_to_user_with_invalid_valid_from(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.get("/users/rbacmanager")
    user = response.json()
    role = await create_and_get_new_role(authorized_client_rbac_manager)
    roles_to_assign = {
        "user_roles": [
            {
                "role_id": role["id"],
                "valid_from": "2026-01-01T00:00:00Z",
                "valid_until": "2026-01-01T00:00:00Z",
            }
        ]
    }
    response = await authorized_client_rbac_manager.post(f"authorization/users/{user['id']}/roles", json=roles_to_assign)
    assert response.status_code == 422
    assert response.json()["detail"] == "Value error, valid_from must be earlier than valid_until for field user_roles"
    user_roles = await authorized_client_rbac_manager.get(f"authorization/users/{user['id']}/roles")
    assert len(user_roles.json()) == 1

    