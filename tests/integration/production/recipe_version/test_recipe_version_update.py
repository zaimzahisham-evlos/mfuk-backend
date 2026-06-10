import pytest

pytestmark = [pytest.mark.asyncio, pytest.mark.usefixtures("seeded_recipe_versions")]

test_payload = {
    "version_code": "TEST_RECIPE_VERSION_001_UPDATE",
    "version_name": "Test Recipe Version 001 Update",
    "change_summary": "Test Recipe Version 001 Change Summary",
    "engineering_reason": "Test Recipe Version 001 Engineering Reason",
}

def assert_recipe_version_updated(response, payload):
    assert response.status_code == 200
    assert response.json()["version_name"] == payload["version_name"]
    assert response.json()["change_summary"] == payload["change_summary"]
    assert response.json()["engineering_reason"] == payload["engineering_reason"]
    assert response.json()["updated_at"] is not None
    assert response.json()["updated_by_id"] is not None

async def test_superadmin_update_recipe_version(authorized_client_superadmin):
    response = await authorized_client_superadmin.patch(f"/production/recipe-versions/TEST_RECIPE_VERSION_001", json=test_payload)
    assert_recipe_version_updated(response, test_payload)
    assert response.json()["version_code"] == "TEST_RECIPE_VERSION_001" # version code is immutable

async def test_admin_update_recipe_version(authorized_client_admin):
    response = await authorized_client_admin.patch(f"/production/recipe-versions/TEST_RECIPE_VERSION_001", json=test_payload)
    assert_recipe_version_updated(response, test_payload)
    assert response.json()["version_code"] == "TEST_RECIPE_VERSION_001" # version code is immutable

async def test_user_no_permission_update_recipe_version(authorized_client_human_no_role):
    response = await authorized_client_human_no_role.patch(f"/production/recipe-versions/TEST_RECIPE_VERSION_001", json=test_payload)
    assert response.status_code == 403
    assert response.json()["detail"] == "User does not have permission to access RECIPE_VERSION_UPDATE"

async def test_update_recipe_version_with_blank_version_name(authorized_client_admin):
    payload = test_payload.copy()
    payload["version_name"] = ""
    response = await authorized_client_admin.patch(f"/production/recipe-versions/TEST_RECIPE_VERSION_001", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"] == "Value error, Value cannot be blank for field version_name"

async def test_update_recipe_version_status_approval_required(authorized_client_admin):
    payload = test_payload.copy() # start with draft status
    response = await authorized_client_admin.get(f"/production/recipe-versions/TEST_RECIPE_VERSION_001")
    assert response.status_code == 200
    assert response.json()["status"] == "Draft"
    assert response.json()["approval_required"] == True

    # update to released directly from draft, should fail because approval is required
    response = await authorized_client_admin.patch(f"/production/recipe-versions/TEST_RECIPE_VERSION_001", json={
        "status": "Released",
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Approval is required to update recipe version from draft to released"

    # update to approved, then to released, should succeed
    response = await authorized_client_admin.patch(f"/production/recipe-versions/TEST_RECIPE_VERSION_001", json={
        "status": "Approved",
    })

    # ensure can update status backwards. e.g, approved -> underreview -> approved -> released
    response = await authorized_client_admin.patch(f"/production/recipe-versions/TEST_RECIPE_VERSION_001", json={
        "status": "UnderReview",
    })
    assert response.status_code == 200
    assert response.json()["status"] == "UnderReview"

    # underreview to released directly, skipping approved again. should fail because approval is required
    response = await authorized_client_admin.patch(f"/production/recipe-versions/TEST_RECIPE_VERSION_001", json={
        "status": "Released",
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Approval is required to update recipe version from underreview to released"

    # then update to approved, should succeed
    response = await authorized_client_admin.patch(f"/production/recipe-versions/TEST_RECIPE_VERSION_001", json={
        "status": "Approved",
    })
    assert response.status_code == 200
    assert response.json()["status"] == "Approved"

    # then update to released, should succeed
    response = await authorized_client_admin.patch(f"/production/recipe-versions/TEST_RECIPE_VERSION_001", json={
        "status": "Released",
    })
    assert response.status_code == 200
    assert response.json()["status"] == "Released"

async def test_update_recipe_version_status_approval_not_required(authorized_client_admin):
    payload = test_payload.copy() # start with draft status
    response = await authorized_client_admin.get(f"/production/recipe-versions/TEST_RECIPE_VERSION_002")
    assert response.status_code == 200
    assert response.json()["status"] == "Draft"
    assert response.json()["approval_required"] == False

    # update to released directly from draft, should succeed because approval is not required
    response = await authorized_client_admin.patch(f"/production/recipe-versions/TEST_RECIPE_VERSION_002", json={
        "status": "Released",
    })
    assert response.status_code == 200
    assert response.json()["status"] == "Released"

    # ensure released version cannot be updated
    response = await authorized_client_admin.patch(f"/production/recipe-versions/TEST_RECIPE_VERSION_002", json={
        "version_name": "Test Recipe Version 002 Update",
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot update a released recipe version"

async def test_update_recipe_version_only_one_released_per_recipe(authorized_client_admin):
    # release recipe version 1. Note: approval is required for released.
    response = await authorized_client_admin.patch(f"/production/recipe-versions/TEST_RECIPE_VERSION_001", json={
        "status": "Approved",
    })
    response = await authorized_client_admin.patch(f"/production/recipe-versions/TEST_RECIPE_VERSION_001", json={
        "status": "Released",
    })
    assert response.json()["status"] == "Released"
    assert response.json()["released_at"] is not None

    # release recipe version 2, version 1 should be superseded
    response = await authorized_client_admin.patch(f"/production/recipe-versions/TEST_RECIPE_VERSION_002", json={
        "status": "Approved",
    })
    response = await authorized_client_admin.patch(f"/production/recipe-versions/TEST_RECIPE_VERSION_002", json={
        "status": "Released",
    })
    assert response.status_code == 200
    assert response.json()["status"] == "Released"
    assert response.json()["released_at"] is not None
    version_2_id = response.json()["id"]

    # get recipe version 1, should be superseded by version 2
    response = await authorized_client_admin.get(f"/production/recipe-versions/TEST_RECIPE_VERSION_001")
    assert response.status_code == 200
    assert response.json()["status"] == "Superseded"
    assert response.json()["superseded_at"] is not None
    assert response.json()["superseded_by_version_id"] == version_2_id

    # get recipe version 2, should be released
    response = await authorized_client_admin.get(f"/production/recipe-versions/TEST_RECIPE_VERSION_002")
    assert response.status_code == 200
    assert response.json()["status"] == "Released"
    assert response.json()["released_at"] is not None

    # released version cannot be updated
    response = await authorized_client_admin.patch(f"/production/recipe-versions/TEST_RECIPE_VERSION_002", json={
        "version_name": "Test Recipe Version 002 Update",
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot update a released recipe version"

    # get recipe -> current_released_version should be version 2
    response = await authorized_client_admin.get(f"/production/recipes/TEST_RECIPE_00")
    assert response.status_code == 200
    assert response.json()["current_released_version"] == "TEST_RECIPE_VERSION_002"