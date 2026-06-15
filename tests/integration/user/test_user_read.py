import pytest
from app.user.models import UserStatus, UserType

pytestmark = pytest.mark.integration

async def test_get_me_authorized(authorized_client_human_no_role):
    response = await authorized_client_human_no_role.get("/users/me")
    assert response.status_code == 200
    assert response.json()["user_code"] == "TESTUSER"
    assert response.json()["full_name"] == "Test User"
    assert response.json()["user_type"] == UserType.HUMAN.value
    assert response.json()["status"] == UserStatus.ACTIVE.value

async def test_get_me_unauthorized(client):
    response = await client.get("/users/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

async def test_get_me_invalid_token(client):
    client.headers["Authorization"] = "Bearer invalidtoken"
    response = await client.get("/users/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"

async def test_get_users_exclude_deleted(authorized_client_user_manager):
    payload = {
        "user_code": "newuser",
        "full_name": "New User",
        "user_type": UserType.HUMAN,
        "status": UserStatus.ACTIVE,
        "password": "password"
    }

    response = await authorized_client_user_manager.post("/users/", json=payload)
    assert response.status_code == 201

    response = await authorized_client_user_manager.get("/users/")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 3 
    # 2 users + 1 new user (superadmin seeded in db_session, user_manager in param + new user)

    response = await authorized_client_user_manager.delete(f"/users/{payload["user_code"]}")
    assert response.status_code == 204

    response = await authorized_client_user_manager.get("/users/")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 2
    assert response.json()["items"][-1]["user_code"] == "SUPERADMIN" # first user because it is seeded in db_session
    assert response.json()["items"][-1]["full_name"] == "Super Admin"
    assert response.json()["items"][-1]["status"] == UserStatus.ACTIVE.value

async def test_get_user_by_user_code(authorized_client_user_manager):
    response = await authorized_client_user_manager.get("/users/usermanager")
    assert response.status_code == 200
    assert response.json()["user_code"] == "USERMANAGER"
    assert response.json()["full_name"] == "User Manager"

async def test_get_deleted_user_by_user_code(authorized_client_user_manager):
    response = await authorized_client_user_manager.delete("/users/usermanager")
    assert response.status_code == 204

    response = await authorized_client_user_manager.get("/users/usermanager")
    assert response.status_code == 404
    assert response.json()["detail"] == "User with user code USERMANAGER not found"

async def test_get_non_existent_user_by_user_code(authorized_client_user_manager):
    response = await authorized_client_user_manager.get("/users/nonexistentuser")
    assert response.status_code == 404
    assert response.json()["detail"] == "User with user code NONEXISTENTUSER not found"

async def test_user_no_role_get_users(authorized_client_human_no_role):
    response = await authorized_client_human_no_role.get("/users/")
    assert response.status_code == 403
    assert response.json()["detail"] == "User does not have permission to access USER_VIEW"

async def test_user_no_role_get_user_by_user_code(authorized_client_human_no_role):
    response = await authorized_client_human_no_role.get("/users/usermanager")
    assert response.status_code == 403
    assert response.json()["detail"] == "User does not have permission to access USER_VIEW"

async def test_superadmin_get_users(authorized_client_superadmin):
    response = await authorized_client_superadmin.get("/users/")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1 # only superadmin user because it is the parameter
    assert response.json()["items"][0]["user_code"] == "SUPERADMIN"
    assert response.json()["items"][0]["full_name"] == "Super Admin"
    assert response.json()["items"][0]["status"] == UserStatus.ACTIVE.value

async def test_superadmin_get_user_by_user_code(authorized_client_superadmin, authorized_client_user_manager):
    response = await authorized_client_superadmin.get("/users/usermanager")
    assert response.status_code == 200
    assert response.json()["user_code"] == "USERMANAGER"
    assert response.json()["full_name"] == "User Manager"

async def test_get_users_with_pagination(authorized_client_admin):
    response = await authorized_client_admin.get("/users/?page=1&limit=1")
    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert response.json()["page"] == 1
    assert response.json()["limit"] == 1
    assert response.json()["total_pages"] == 2
    assert len(response.json()["items"]) == 1

async def test_get_users_search_not_limited_by_page(authorized_client_admin):
    response = await authorized_client_admin.get("/users/?search=super&page=1&limit=1")
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["user_code"] == "SUPERADMIN"
    assert response.json()["items"][0]["full_name"] == "Super Admin"
    assert response.json()["items"][0]["status"] == UserStatus.ACTIVE.value

    response = await authorized_client_admin.get("/users/?search=admin&page=1&limit=1")
    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert response.json()["items"][0]["user_code"] == "ADMIN"
    assert response.json()["items"][0]["full_name"] == "Admin"
    assert response.json()["items"][0]["status"] == UserStatus.ACTIVE.value