import pytest

pytestmark = pytest.mark.integration

async def test_login_human_with_valid_credentials(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.post("/auth/login", json={
        "user_code": "rbacmanager",
        "password": "password"
    })
    assert response.status_code == 200
    assert response.json()["access_token"] is not None
    assert response.json()["refresh_token"] is not None
    assert response.json()["token_type"] == "bearer"
    
async def test_login_human_with_invalid_credentials(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.post("/auth/login", json={
        "user_code": "rbacmanager",
        "password": "invalid_password"
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"

async def test_login_with_blank_user_code(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.post("/auth/login", json={
        "user_code": "",
        "password": "password"
    })
    assert response.status_code == 422
    assert response.json()["detail"] == "Value error, user_code cannot be blank for field user_code"
    
async def test_login_with_blank_password(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.post("/auth/login", json={
        "user_code": "rbacmanager",
        "password": ""
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"
    
async def test_login_with_invalid_user_code(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.post("/auth/login", json={
        "user_code": "invalid_user_code",
        "password": "password"
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"
    
async def test_login_with_inactive_user(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.patch("/users/rbacmanager", json={
        "status": "Inactive"
    })
    assert response.status_code == 200
    assert response.json()["status"] == "Inactive"
    response = await authorized_client_rbac_manager.post("/auth/login", json={
        "user_code": "rbacmanager",
        "password": "password"
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "User is inactive and cannot login. Please contact support."

async def test_login_with_suspended_user(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.patch("/users/rbacmanager", json={
        "status": "Suspended"
    })
    assert response.status_code == 200
    assert response.json()["status"] == "Suspended"
    response = await authorized_client_rbac_manager.post("/auth/login", json={
        "user_code": "rbacmanager",
        "password": "password"
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "User is suspended and cannot login. Please contact support."

async def test_login_with_deleted_user(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.delete("/users/rbacmanager")
    assert response.status_code == 204
    response = await authorized_client_rbac_manager.post("/auth/login", json={
        "user_code": "rbacmanager",
        "password": "password"
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"

async def test_login_non_human_with_valid_credentials(authorized_client_non_human):
    response = await authorized_client_non_human.post("/auth/login", json={
        "user_code": "testusernonhuman",
        "password": ""
    })
    assert response.status_code == 200
    assert response.json()["access_token"] is not None
    assert response.json()["refresh_token"] is not None
    assert response.json()["token_type"] == "bearer"
    
async def test_login_non_human_with_invalid_credentials(authorized_client_non_human):
    response = await authorized_client_non_human.post("/auth/login", json={
        "user_code": "testusernonhuman",
        "password": "invalid_password"
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"