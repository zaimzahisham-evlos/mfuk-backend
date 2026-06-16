import pytest

@pytest.mark.asyncio

def assert_permission_to_role_assigned(role_permission):
    assert role_permission["role_permission"]["status"] == "Active"
    assert role_permission["role_permission"]["effect"] == "Allow"
    assert role_permission["role_permission"]["priority"] == 100
    assert role_permission["role_permission"]["valid_from"] is None
    assert role_permission["role_permission"]["valid_until"] is None
    assert role_permission["role_permission"]["notes"] is None
    assert role_permission["role_permission"]["created_by_id"] is not None
    assert role_permission["role_permission"]["created_at"] is not None
    assert role_permission["role_permission"]["updated_at"] is None
    assert role_permission["role_permission"]["deleted_at"] is None
    assert role_permission["role_permission"]["deleted_by_id"] is None

async def test_superadmin_assign_permissions_to_role(authorized_client_superadmin):
    role = await authorized_client_superadmin.get("/authorization/roles/superadmin")
    role_id = role.json()["id"]
    permissions = await authorized_client_superadmin.get("/authorization/permissions?modules=role&modules=permission")
    permissions = permissions.json()["items"]
    response = await authorized_client_superadmin.post(f"/authorization/roles/{role_id}/permissions", json={
        "role_permissions": [
            {
                "permission_id": permission["id"],
            }
            for permission in permissions
        ]
    })
    assert response.status_code == 200
    assert response.json()["role_id"] == role_id
    assert len(response.json()["outcomes"]) == len(permissions)
    for outcome in response.json()["outcomes"]:
        assert_permission_to_role_assigned(outcome)

async def test_rbac_manager_assign_permissions_to_role(authorized_client_rbac_manager):
    role = await authorized_client_rbac_manager.get("/authorization/roles/superadmin")
    role_id = role.json()["id"]
    permissions = await authorized_client_rbac_manager.get("/authorization/permissions?modules=role&modules=permission")
    permissions = permissions.json()["items"]
    response = await authorized_client_rbac_manager.post(f"/authorization/roles/{role_id}/permissions", json={
        "role_permissions": [
            {
                "permission_id": permission["id"],
            }
            for permission in permissions
        ]
    })
    assert response.status_code == 200
    assert response.json()["role_id"] == role_id
    assert len(response.json()["outcomes"]) == len(permissions)
    for outcome in response.json()["outcomes"]:
        assert_permission_to_role_assigned(outcome)

async def test_assign_permissions_to_role_duplicate_in_payload(authorized_client_rbac_manager):
    role = await authorized_client_rbac_manager.get("/authorization/roles/superadmin")
    role_id = role.json()["id"]
    permissions = await authorized_client_rbac_manager.get("/authorization/permissions?modules=role&modules=permission")
    permissions = permissions.json()["items"]
    response = await authorized_client_rbac_manager.post(f"/authorization/roles/{role_id}/permissions", json={
        "role_permissions": [
            {
                "permission_id": permission["id"],
            }
            for permission in permissions
        ] * 2
    })
    assert response.status_code == 200
    assert response.json()["role_id"] == role_id
    assert len(response.json()["outcomes"]) == len(permissions) * 2
    for outcome in response.json()["outcomes"]:
        if outcome["status"] == "duplicate_entry":
            continue
        assert_permission_to_role_assigned(outcome)

    role_permissions = await authorized_client_rbac_manager.get(f"/authorization/roles/{role_id}/permissions") 
    assert len(role_permissions.json()) == len(permissions)

async def test_assign_permissions_to_role_same_permission_different_priority(authorized_client_rbac_manager):
    role = await authorized_client_rbac_manager.get("/authorization/roles/superadmin")
    role_id = role.json()["id"]
    permissions = await authorized_client_rbac_manager.get("/authorization/permissions?modules=role&modules=permission")
    permissions = permissions.json()["items"]
    response = await authorized_client_rbac_manager.post(f"/authorization/roles/{role_id}/permissions", json={
        "role_permissions": [
            {
                "permission_id": permissions[0]["id"],
            },
            {
                "permission_id": permissions[0]["id"],
                "priority": 90,
            }
        ]
    })
    assert response.status_code == 200
    assert response.json()["role_id"] == role_id
    assert len(response.json()["outcomes"]) == 2
    
    role_permissions = await authorized_client_rbac_manager.get(f"/authorization/roles/{role_id}/permissions") 
    assert len(role_permissions.json()) == 2

async def test_assign_permissions_to_role_with_status_deleted(authorized_client_rbac_manager):
    role = await authorized_client_rbac_manager.get("/authorization/roles/superadmin")
    role_id = role.json()["id"]
    permissions = await authorized_client_rbac_manager.get("/authorization/permissions?modules=role&modules=permission")
    permissions = permissions.json()["items"]
    response = await authorized_client_rbac_manager.post(f"/authorization/roles/{role_id}/permissions", json={
        "role_permissions": [
            {
                "permission_id": permission["id"],
                "status": "Deleted",
            }
            for permission in permissions
        ]
    })
    assert response.status_code == 422
    assert response.json()["detail"] == "Value error, Cannot assign a role permission with status DELETED for field role_permissions"

async def test_assign_permissions_to_role_not_found_permission(authorized_client_rbac_manager):
    role = await authorized_client_rbac_manager.get("/authorization/roles/superadmin")
    role_id = role.json()["id"]
    response = await authorized_client_rbac_manager.post(f"/authorization/roles/{role_id}/permissions", json={
        "role_permissions": [
            {
                "permission_id": 999999999999999999,
            }
        ]
    })
    assert response.status_code == 200
    assert response.json()["role_id"] == role_id
    assert len(response.json()["outcomes"]) == 1
    assert response.json()["outcomes"][0]["status"] == "not_found_permission"
    assert response.json()["outcomes"][0]["message"] == "Permission with ID 999999999999999999 not found"

    role_permissions = await authorized_client_rbac_manager.get(f"/authorization/roles/{role_id}/permissions") 
    assert len(role_permissions.json()) == 0 # no permissions assigned to the role

async def test_assign_permissions_to_role_not_found_role(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.post(f"/authorization/roles/999999999999999999/permissions", json={
        "role_permissions": [
            {
                "permission_id": 1,
            }
        ]
    })
    assert response.status_code == 404
    assert response.json()["detail"] == "Role with ID 999999999999999999 not found"

async def test_assign_permissions_to_role_already_assigned(authorized_client_rbac_manager):
    role = await authorized_client_rbac_manager.get("/authorization/roles/rbac_manager")
    role_id = role.json()["id"]
    permissions = await authorized_client_rbac_manager.get("/authorization/permissions?modules=role&modules=permission")
    permissions = permissions.json()["items"]
    response = await authorized_client_rbac_manager.post(f"/authorization/roles/{role_id}/permissions", json={
        "role_permissions": [
            {
                "permission_id": permission["id"],
            }
            for permission in permissions
        ]
    })
    assert response.status_code == 200
    assert response.json()["role_id"] == role_id
    assert len(response.json()["outcomes"]) == len(permissions)
    for outcome in response.json()["outcomes"]:
        if outcome["status"] == "already_assigned":
            continue
        assert_permission_to_role_assigned(outcome)

    role_permissions = await authorized_client_rbac_manager.get(f"/authorization/roles/{role_id}/permissions") 
    assert len(role_permissions.json()) >= len(permissions)

async def test_assign_permissions_to_role_already_assigned_different_status(authorized_client_rbac_manager):
    role = await authorized_client_rbac_manager.get("/authorization/roles/rbac_manager")
    role_id = role.json()["id"]
    permissions = await authorized_client_rbac_manager.get("/authorization/permissions?modules=role&modules=permission")
    permissions = permissions.json()["items"]
    response = await authorized_client_rbac_manager.post(f"/authorization/roles/{role_id}/permissions", json={
        "role_permissions": [
            {
                "permission_id": permissions[0]["id"],
                "status": "Inactive",
            }
        ]
    })
    assert response.status_code == 200
    assert response.json()["outcomes"][0]["status"] == "already_assigned"

async def test_assign_permissions_to_role_invalid_status(authorized_client_rbac_manager):
    role = await authorized_client_rbac_manager.get("/authorization/roles/superadmin")
    role_id = role.json()["id"]
    permissions = await authorized_client_rbac_manager.get("/authorization/permissions?modules=role&modules=permission")
    permissions = permissions.json()["items"]
    response = await authorized_client_rbac_manager.post(f"/authorization/roles/{role_id}/permissions", json={
        "role_permissions": [
            {
                "permission_id": permission["id"],
                "status": "Invalid",
            }
            for permission in permissions
        ]
    })
    assert response.status_code == 422
    assert response.json()["detail"] == "Input should be 'Active', 'Inactive', 'Deleted' or 'Suspended' for field role_permissions[0].status"

async def test_assign_permissions_to_role_invalid_effect(authorized_client_rbac_manager):
    role = await authorized_client_rbac_manager.get("/authorization/roles/superadmin")
    role_id = role.json()["id"]
    permissions = await authorized_client_rbac_manager.get("/authorization/permissions?modules=role&modules=permission")
    permissions = permissions.json()["items"]
    response = await authorized_client_rbac_manager.post(f"/authorization/roles/{role_id}/permissions", json={
        "role_permissions": [
            {
                "permission_id": permission["id"],
                "effect": "Invalid",
            }
            for permission in permissions
        ]
    })
    assert response.status_code == 422
    assert response.json()["detail"] == "Input should be 'Allow' or 'Deny' for field role_permissions[0].effect"

async def test_assign_permissions_to_role_invalid_priority(authorized_client_rbac_manager):
    role = await authorized_client_rbac_manager.get("/authorization/roles/superadmin")
    role_id = role.json()["id"]
    permissions = await authorized_client_rbac_manager.get("/authorization/permissions?modules=role&modules=permission")
    permissions = permissions.json()["items"]
    response = await authorized_client_rbac_manager.post(f"/authorization/roles/{role_id}/permissions", json={
        "role_permissions": [
            {
                "permission_id": permission["id"],
                "priority": -1,
            }
        ] for permission in permissions
    })
    assert response.status_code == 422
    assert response.json()["detail"] == "Input should be greater than or equal to 0 for field role_permissions[0].priority"

async def test_assign_permissions_to_role_all_fields(authorized_client_rbac_manager):
    role = await authorized_client_rbac_manager.get("/authorization/roles/superadmin")
    role_id = role.json()["id"]
    permissions = await authorized_client_rbac_manager.get("/authorization/permissions?modules=role&modules=permission")
    permissions = permissions.json()["items"]
    response = await authorized_client_rbac_manager.post(f"/authorization/roles/{role_id}/permissions", json={
        "role_permissions": [
            {
                "permission_id": permissions[0]["id"],
                "status": "Inactive",
                "effect": "Deny",
                "priority": 90,
                "notes": "Test notes",
            }
        ]
    })
    assert response.status_code == 200
    assert response.json()["role_id"] == role_id
    assert len(response.json()["outcomes"]) == 1
    for outcome in response.json()["outcomes"]:
        assert outcome["status"] == "assigned"
        assert outcome["role_permission"]["permission_id"] == permissions[0]["id"]
        assert outcome["role_permission"]["status"] == "Inactive"
        assert outcome["role_permission"]["effect"] == "Deny"
        assert outcome["role_permission"]["priority"] == 90
        assert outcome["role_permission"]["notes"] == "Test notes"
        assert outcome["role_permission"]["created_by_id"] is not None
        assert outcome["role_permission"]["created_at"] is not None
        assert outcome["role_permission"]["updated_at"] is None
        assert outcome["role_permission"]["deleted_at"] is None

    role_permissions = await authorized_client_rbac_manager.get(f"/authorization/roles/{role_id}/permissions") 
    assert len(role_permissions.json()) == 1

    role_permission = await authorized_client_rbac_manager.get(f"/authorization/role-permission/{role_permissions.json()[0]["id"]}")
    assert role_permission.json()["status"] == "Inactive"
    assert role_permission.json()["effect"] == "Deny"
    assert role_permission.json()["priority"] == 90
    assert role_permission.json()["notes"] == "Test notes"
    assert role_permission.json()["created_by_id"] is not None
    assert role_permission.json()["created_at"] is not None
    assert role_permission.json()["updated_at"] is None
    assert role_permission.json()["deleted_at"] is None
    assert role_permission.json()["deleted_by_id"] is None

async def test_assign_higher_priority_permission_to_deny_role_permission(authorized_client_rbac_manager):
    role = await authorized_client_rbac_manager.get("/authorization/roles/rbac_manager")
    role_id = role.json()["id"]
    permissions = await authorized_client_rbac_manager.get("/authorization/permissions?modules=role&modules=permission")
    permissions = permissions.json()["items"]
    permission_id = None
    for permission in permissions:
        if permission["permission_code"] == "PERMISSION_VIEW":
            permission_id = permission["id"]
            break
    
    response = await authorized_client_rbac_manager.post(f"/authorization/roles/{role_id}/permissions", json={
        "role_permissions": [
            {
                "permission_id": permission_id,
                "priority": 90,
                "effect": "Deny",
            },
        ]
    })
    assert response.status_code == 200

    response = await authorized_client_rbac_manager.get("authorization/permissions")
    assert response.status_code == 403
    assert response.json()["detail"] == "User does not have permission to access PERMISSION_VIEW"