import pytest
from app.user.models import UserStatus, UserType

pytestmark = pytest.mark.integration

async def test_update_user_self(authorized_client_user_manager):
    response = await authorized_client_user_manager.patch("/users/usermanager", json={
        "full_name": "User Manager Updated",
        "status": UserStatus.INACTIVE,
    })
    assert response.status_code == 200
    assert response.json()["full_name"] == "User Manager Updated"
    assert response.json()["user_code"] == "USERMANAGER"
    assert response.json()["user_type"] == UserType.HUMAN.value
    assert response.json()["status"] == UserStatus.INACTIVE.value
    assert response.json()["updated_at"] is not None
    assert response.json()["updated_by_id"] is not None

async def test_user_with_permission_update_user_other(authorized_client_user_manager):
    payload = {
        "user_code": "newuser",
        "full_name": "New User",
        "user_type": UserType.HUMAN,
        "status": UserStatus.ACTIVE,
        "password": "password"
    }
    response = await authorized_client_user_manager.post("/users/", json=payload)
    assert response.status_code == 201

    response = await authorized_client_user_manager.patch("/users/newuser", json={
        "full_name": "New User Updated",
    })
    assert response.status_code == 200
    assert response.json()["full_name"] == "New User Updated"
    assert response.json()["user_code"] == "NEWUSER"
    assert response.json()["user_type"] == UserType.HUMAN.value
    assert response.json()["status"] == UserStatus.ACTIVE.value
    assert response.json()["updated_at"] is not None

async def test_user_without_permission_update_user_other(authorized_client_human_no_role):
    response = await authorized_client_human_no_role.patch("/users/newuser", json={
        "full_name": "New User Updated",
    })
    assert response.status_code == 403
    assert response.json()["detail"] == "You are not allowed to update this user"

async def test_user_without_permission_update_self(authorized_client_human_no_role):
    response = await authorized_client_human_no_role.patch("/users/testuser", json={
        "full_name": "User Manager Updated",
    })
    assert response.status_code == 200
    assert response.json()["full_name"] == "User Manager Updated"

async def test_update_user_full_name_blank(authorized_client_user_manager):
    response = await authorized_client_user_manager.patch("/users/testuser", json={
        "full_name": " ",
    })
    assert response.status_code == 422
    assert response.json()["detail"] == "Value error, Value cannot be blank for field full_name"

async def test_update_user_user_type_invalid(authorized_client_user_manager):
    response = await authorized_client_user_manager.patch("/users/testuser", json={
        "user_type": "Invalid",
    })
    assert response.status_code == 422
    assert response.json()["detail"] == "Input should be 'Human', 'System', 'Service', 'Robot' or 'PLC' for field user_type"

async def test_update_user_human_without_password(authorized_client_user_manager):
    response = await authorized_client_user_manager.patch("/users/usermanager", json={
        "password": None,
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Human users must have a password hash"

async def test_update_user_human_with_password(authorized_client_user_manager):
    response = await authorized_client_user_manager.patch("/users/usermanager", json={
        "password": "newpassword",
    })
    assert response.status_code == 200

async def test_update_user_non_human_with_password(authorized_client_non_human):
    response = await authorized_client_non_human.patch("/users/testusernonhuman", json={
        "password": "newpassword",
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Password is not allowed for user type System"
