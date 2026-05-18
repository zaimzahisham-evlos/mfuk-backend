import pytest

@pytest.mark.asyncio

def assert_permission_to_role_revoked(outcome):
    assert outcome["status"] == "revoked"
    assert outcome["role_permission"]["status"] == "Deleted"
    assert outcome["role_permission"]["deleted_at"] is not None
    assert outcome["role_permission"]["deleted_by_id"] is not None
    assert outcome["role_permission"]["deleted_at"] is not None
    assert outcome["role_permission"]["updated_by_id"] is not None
    assert outcome["role_permission"]["updated_at"] is not None

async def test_superadmin_revoke_permissions_from_role(authorized_client_rbac_manager, authorized_client_superadmin):
    role = await authorized_client_superadmin.get("/authorization/roles/rbac_manager")
    role_id = role.json()["id"]
    role_permissions = await authorized_client_superadmin.get(f"/authorization/roles/{role_id}/permissions")
    role_permissions = role_permissions.json()
    response = await authorized_client_superadmin.patch(f"/authorization/roles/{role_id}/permissions/revoke", json={
        "role_permissions": [
            {
                "role_permission_id": role_permissions[0]["id"],
                "notes": "Test notes"
            }
        ]
    })
    assert response.status_code == 200
    assert response.json()["role_id"] == role_id
    assert len(response.json()["outcomes"]) == 1
    assert_permission_to_role_revoked(response.json()["outcomes"][0])

async def test_rbac_manager_revoke_permissions_from_role(authorized_client_rbac_manager):
    role = await authorized_client_rbac_manager.get("/authorization/roles/rbac_manager")
    role_id = role.json()["id"]
    role_permissions = await authorized_client_rbac_manager.get(f"/authorization/roles/{role_id}/permissions")
    role_permissions = role_permissions.json()
    response = await authorized_client_rbac_manager.patch(f"/authorization/roles/{role_id}/permissions/revoke", json={
        "role_permissions": [
            {
                "role_permission_id": role_permissions[0]["id"],
                "notes": "Test notes"
            }
        ]
    })
    assert response.status_code == 200
    assert response.json()["role_id"] == role_id
    assert len(response.json()["outcomes"]) == 1
    assert_permission_to_role_revoked(response.json()["outcomes"][0])

async def test_revoke_permissions_from_role_duplicate_in_payload(authorized_client_rbac_manager):
    role = await authorized_client_rbac_manager.get("/authorization/roles/rbac_manager")
    role_id = role.json()["id"]
    initial_role_permissions = await authorized_client_rbac_manager.get(f"/authorization/roles/{role_id}/permissions")
    initial_role_permissions = initial_role_permissions.json()
    response = await authorized_client_rbac_manager.patch(f"/authorization/roles/{role_id}/permissions/revoke", json={
        "role_permissions": [
            {
                "role_permission_id": initial_role_permissions[0]["id"],
                "notes": "Test notes"
            }
        ] * 2
    })
    assert response.status_code == 200
    assert response.json()["role_id"] == role_id
    assert len(response.json()["outcomes"]) == 2
    for outcome in response.json()["outcomes"]:
        if outcome["status"] == "duplicate_entry":
            continue
        assert_permission_to_role_revoked(outcome)

    final_role_permissions = await authorized_client_rbac_manager.get(f"/authorization/roles/{role_id}/permissions") 
    final_role_permissions = final_role_permissions.json()
    assert len(final_role_permissions) == len(initial_role_permissions) - 1 # one permission should be revoked


async def test_revoke_permissions_from_role_not_found_permission(authorized_client_rbac_manager):
    role = await authorized_client_rbac_manager.get("/authorization/roles/rbac_manager")
    role_id = role.json()["id"]
    response = await authorized_client_rbac_manager.patch(f"/authorization/roles/{role_id}/permissions/revoke", json={
        "role_permissions": [
            {
                "role_permission_id": 999,
                "notes": "Test notes"
            }
        ]
    })
    assert response.status_code == 200
    assert response.json()["role_id"] == role_id
    assert len(response.json()["outcomes"]) == 1
    assert response.json()["outcomes"][0]["status"] == "not_found_role_permission"
    assert response.json()["outcomes"][0]["message"] == "Role permission with ID 999 not found"

async def test_revoke_permissions_from_role_not_found_role(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.patch(f"/authorization/roles/999/permissions/revoke", json={
        "role_permissions": [
            {
                "role_permission_id": 1,
                "notes": "Test notes"
            }
        ]
    })
    assert response.status_code == 404
    assert response.json()["detail"] == "Role with ID 999 not found"

async def test_revoke_permissions_from_role_already_revoked(authorized_client_rbac_manager):
    role = await authorized_client_rbac_manager.get("/authorization/roles/rbac_manager")
    role_id = role.json()["id"]
    role_permissions = await authorized_client_rbac_manager.get(f"/authorization/roles/{role_id}/permissions")
    role_permissions = role_permissions.json()
    role_permission_ids = [role_permissions[0]["id"]]
    response = await authorized_client_rbac_manager.patch(f"/authorization/roles/{role_id}/permissions/revoke", json={
        "role_permissions": [
            {
                "role_permission_id": role_permissions[0]["id"],
                "notes": "Test notes"
            }
        ]
    })
    assert response.status_code == 200
    assert response.json()["outcomes"][0]["status"] == "revoked"

    response = await authorized_client_rbac_manager.patch(f"/authorization/roles/{role_id}/permissions/revoke", json={
        "role_permissions": [
            {
                "role_permission_id": role_permissions[0]["id"],
                "notes": "Test notes"
            }
        ]
    })
    assert response.status_code == 200
    assert response.json()["outcomes"][0]["status"] == "not_found_role_permission"
    assert response.json()["outcomes"][0]["message"] == f"Role permission with ID {role_permission_ids[0]} not found"

