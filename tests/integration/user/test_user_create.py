import pytest
from app.user.models import UserStatus, UserType

pytestmark = pytest.mark.integration

new_user_payload = {
        "user_code": "newuser",
        "full_name": "New User",
        "user_type": UserType.HUMAN,
        "status": UserStatus.ACTIVE,
        "password": "password"
    }

def assert_user_created(response, payload):
    assert response.status_code == 201
    assert response.json()["user_code"] == payload["user_code"].upper()
    assert response.json()["full_name"] == payload["full_name"]
    assert response.json()["user_type"] == payload["user_type"].value
    assert response.json()["status"] == payload["status"].value
    assert response.json()["created_by_id"] is not None
    assert response.json()["created_at"] is not None
    assert response.json()["updated_at"] is None
    assert response.json()["deleted_at"] is None
    assert response.json()["deleted_by_id"] is None

def assert_user_exists(response, payload):
    assert response.status_code == 200
    assert response.json()["user_code"] == payload["user_code"].upper()
    assert response.json()["full_name"] == payload["full_name"]
    assert response.json()["user_type"] == payload["user_type"].value
    assert response.json()["status"] == payload["status"].value
    assert response.json()["created_by_id"] is not None

async def test_superadmin_create_user(authorized_client_superadmin):
    
    response = await authorized_client_superadmin.post("/users/", json=new_user_payload)
    assert_user_created(response, new_user_payload)
    
    result = await authorized_client_superadmin.get(f"/users/{new_user_payload["user_code"]}")
    assert_user_exists(result, new_user_payload)

async def test_user_with_permission_create_user(authorized_client_user_manager):
    response = await authorized_client_user_manager.post("/users/", json=new_user_payload)
    assert_user_created(response, new_user_payload)

    result = await authorized_client_user_manager.get(f"/users/{new_user_payload["user_code"]}")
    assert_user_exists(result, new_user_payload)

async def test_user_without_permission_create_user(authorized_client_human_no_role):
    response = await authorized_client_human_no_role.post("/users/", json=new_user_payload)
    assert response.status_code == 403
    assert response.json()["detail"] == "User does not have permission to access USER_CREATE"

async def test_create_user_human_without_password(authorized_client_user_manager):
    payload = new_user_payload.copy()
    payload["password"] = None
    response = await authorized_client_user_manager.post("/users/", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Password is required for user type Human"

async def test_create_user_non_human_with_password(authorized_client_user_manager):
    payload = new_user_payload.copy()
    payload["user_type"] = UserType.SYSTEM
    payload["password"] = "password"
    response = await authorized_client_user_manager.post("/users/", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Password is not allowed for user type System"

async def test_create_user_non_human_without_password(authorized_client_user_manager):
    payload = new_user_payload.copy()
    payload["user_type"] = UserType.SYSTEM
    payload["password"] = None
    response = await authorized_client_user_manager.post("/users/", json=payload)
    assert_user_created(response, payload)
    result = await authorized_client_user_manager.get(f"/users/{payload["user_code"]}")
    assert_user_exists(result, payload)

async def test_create_user_duplicate_user_code(authorized_client_user_manager):
    payload = new_user_payload.copy()
    payload["user_code"] = "usermanager"
    response = await authorized_client_user_manager.post("/users/", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "User with user code USERMANAGER already exists"

async def test_create_user_with_deleted_user_code(authorized_client_user_manager):
    response = await authorized_client_user_manager.post("/users/", json=new_user_payload)
    assert response.status_code == 201
    response = await authorized_client_user_manager.delete(f"/users/{new_user_payload["user_code"]}")
    assert response.status_code == 204
    response = await authorized_client_user_manager.get(f"/users/{new_user_payload["user_code"]}")
    assert response.status_code == 404
    assert response.json()["detail"] == "User with user code NEWUSER not found"
    response = await authorized_client_user_manager.post("/users/", json=new_user_payload)
    assert response.status_code == 201
    response = await authorized_client_user_manager.get(f"/users/{new_user_payload["user_code"]}")
    assert_user_exists(response, new_user_payload)

async def test_create_user_with_blank_user_code(authorized_client_user_manager):
    payload = new_user_payload.copy()
    payload["user_code"] = " "
    response = await authorized_client_user_manager.post("/users/", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"] == "Value error, Value cannot be blank for field user_code"

async def test_create_user_duplicate_user_code_with_leading_trailing_space(authorized_client_user_manager):
    payload = new_user_payload.copy()
    payload["user_code"] = " usermanager "
    response = await authorized_client_user_manager.post("/users/", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "User with user code USERMANAGER already exists"

async def test_create_user_with_blank_full_name(authorized_client_user_manager):
    payload = new_user_payload.copy()
    payload["full_name"] = " "
    response = await authorized_client_user_manager.post("/users/", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"] == "Value error, Value cannot be blank for field full_name"

async def test_create_user_with_invalid_user_type(authorized_client_user_manager):
    payload = new_user_payload.copy()
    payload["user_type"] = "invalid"
    response = await authorized_client_user_manager.post("/users/", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"] == "Input should be 'Human', 'System', 'Service', 'Robot' or 'PLC' for field user_type"

async def test_create_user_with_invalid_status(authorized_client_user_manager):
    payload = new_user_payload.copy()
    payload["status"] = "invalid"
    response = await authorized_client_user_manager.post("/users/", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"] == "Input should be 'Active', 'Inactive', 'Suspended' or 'Deleted' for field status"

async def test_create_user_with_deleted_status(authorized_client_user_manager):
    payload = new_user_payload.copy()
    payload["status"] = UserStatus.DELETED
    response = await authorized_client_user_manager.post("/users/", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot create a user with status Deleted"

async def test_create_user_with_status_not_deleted_or_active(authorized_client_user_manager):
    payload = new_user_payload.copy()
    payload["status"] = UserStatus.INACTIVE
    response = await authorized_client_user_manager.post("/users/", json=payload)
    assert_user_created(response, payload)
    result = await authorized_client_user_manager.get(f"/users/{payload["user_code"]}")
    assert_user_exists(result, payload)

async def test_create_user_with_short_password(authorized_client_user_manager):
    payload = new_user_payload.copy()
    payload["password"] = "1234567"
    response = await authorized_client_user_manager.post("/users/", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"] == "String should have at least 8 characters for field password"

async def test_create_user_with_password_too_long(authorized_client_user_manager):
    password = "0123456789"*11
    payload = new_user_payload.copy()
    payload["password"] = password
    response = await authorized_client_user_manager.post("/users/", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"] == "String should have at most 100 characters for field password"

