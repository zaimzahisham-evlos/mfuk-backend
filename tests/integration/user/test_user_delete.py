import pytest

pytestmark = pytest.mark.integration

async def test_delete_user_self(authorized_client_user_manager):
    response = await authorized_client_user_manager.delete("/users/usermanager")
    assert response.status_code == 204

async def test_delete_user_other(authorized_client_human_no_role, authorized_client_user_manager):
    response = await authorized_client_user_manager.delete("/users/testuser")
    assert response.status_code == 204

async def test_delete_user_without_permission(authorized_client_human_no_role):
    response = await authorized_client_human_no_role.delete("/users/usermanager")
    assert response.status_code == 403
    assert response.json()["detail"] == "User does not have permission to access USER_DELETE"

async def test_delete_user_without_permission_self(authorized_client_human_no_role):
    response = await authorized_client_human_no_role.delete("/users/testuser")
    assert response.status_code == 403
    assert response.json()["detail"] == "User does not have permission to access USER_DELETE"