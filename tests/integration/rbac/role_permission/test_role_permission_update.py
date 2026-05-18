import pytest

pytestmark = pytest.mark.asyncio

test_payload = {
    "status": "Inactive",
    "effect": "Deny",
    "priority": 90,
    "notes": "updated notes"
}

def assert_role_permission_updated(response, payload):
    assert response.status_code == 200
    assert response.json()["status"] == payload["status"]
    assert response.json()["effect"] == payload["effect"]
    assert response.json()["priority"] == payload["priority"]
    assert response.json()["notes"] == payload["notes"]

async def test_superadmin_update_role_permission(authorized_client_rbac_manager, authorized_client_superadmin):
    role = await authorized_client_superadmin.get("/authorization/roles/rbac_manager")
    role_id = role.json()["id"]
    role_permissions = await authorized_client_superadmin.get(f"/authorization/roles/{role_id}/permissions")
    role_permissions = role_permissions.json()
    role_permission_id = role_permissions[0]["id"]
    response = await authorized_client_superadmin.patch(f"/authorization/role-permission/{role_permission_id}", json=test_payload)
    assert_role_permission_updated(response, test_payload)

async def test_rbac_manager_update_role_permission(authorized_client_rbac_manager):
    role = await authorized_client_rbac_manager.get("/authorization/roles/rbac_manager")
    role_id = role.json()["id"]
    role_permissions = await authorized_client_rbac_manager.get(f"/authorization/roles/{role_id}/permissions")
    role_permissions = role_permissions.json()
    role_permission_id = role_permissions[0]["id"]
    response = await authorized_client_rbac_manager.patch(f"/authorization/role-permission/{role_permission_id}", json=test_payload)
    assert_role_permission_updated(response, test_payload)

async def test_update_role_permission_different_priority_to_same_priority(authorized_client_rbac_manager):
    role = await authorized_client_rbac_manager.get("/authorization/roles/rbac_manager")
    role_id = role.json()["id"]
    role_permissions = await authorized_client_rbac_manager.get(f"/authorization/roles/{role_id}/permissions")
    role_permissions = role_permissions.json()
    role_permission_id = role_permissions[0]["id"]

    # assign a new role permission with the same permission id but different priority
    response = await authorized_client_rbac_manager.post(f"/authorization/roles/{role_id}/permissions", json={
        "role_permissions": [
            {
                "permission_id": role_permissions[0]["permission_id"],
                "priority": 90,
            }
        ]
    })
    assert response.status_code == 200
    assert response.json()["role_id"] == role_id
    assert len(response.json()["outcomes"]) == 1
    assert response.json()["outcomes"][0]["status"] == "assigned"
    assert response.json()["outcomes"][0]["role_permission"]["id"] != role_permission_id

    # update the role permission with the same priority
    response = await authorized_client_rbac_manager.patch(f"/authorization/role-permission/{role_permission_id}", json={
        "priority": 90
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid role permission payload or conflicting role permission data"

async def test_update_role_permission_not_found(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.patch("/authorization/role-permission/999999", json=test_payload)
    assert response.status_code == 404
    assert response.json()["detail"] == "Role permission with ID 999999 not found"


async def test_update_role_permission_invalid_status(authorized_client_rbac_manager):
    role = await authorized_client_rbac_manager.get("/authorization/roles/rbac_manager")
    role_id = role.json()["id"]
    role_permissions = await authorized_client_rbac_manager.get(f"/authorization/roles/{role_id}/permissions")
    role_permissions = role_permissions.json()
    role_permission_id = role_permissions[0]["id"]
    response = await authorized_client_rbac_manager.patch(f"/authorization/role-permission/{role_permission_id}", json={
        "status": "Invalid",
    })
    assert response.status_code == 422
    assert response.json()["detail"] == "Input should be 'Active', 'Inactive', 'Deleted' or 'Suspended' for field status"

async def test_update_role_permission_invalid_effect(authorized_client_rbac_manager):
    role = await authorized_client_rbac_manager.get("/authorization/roles/rbac_manager")
    role_id = role.json()["id"]
    role_permissions = await authorized_client_rbac_manager.get(f"/authorization/roles/{role_id}/permissions")
    role_permissions = role_permissions.json()
    role_permission_id = role_permissions[0]["id"]
    response = await authorized_client_rbac_manager.patch(f"/authorization/role-permission/{role_permission_id}", json={
        "effect": "Invalid",
    })
    assert response.status_code == 422
    assert response.json()["detail"] == "Input should be 'Allow' or 'Deny' for field effect"

async def test_update_role_permission_invalid_priority(authorized_client_rbac_manager):
    role = await authorized_client_rbac_manager.get("/authorization/roles/rbac_manager")
    role_id = role.json()["id"]
    role_permissions = await authorized_client_rbac_manager.get(f"/authorization/roles/{role_id}/permissions")
    role_permissions = role_permissions.json()
    role_permission_id = role_permissions[0]["id"]
    response = await authorized_client_rbac_manager.patch(f"/authorization/role-permission/{role_permission_id}", json={
        "priority": -1,
    })
    assert response.status_code == 422
    assert response.json()["detail"] == "Input should be greater than or equal to 0 for field priority"