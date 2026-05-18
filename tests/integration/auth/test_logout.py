import pytest
import jwt
from datetime import datetime, timedelta, UTC
from app.core.config import settings
from uuid import uuid4
import time

pytestmark = pytest.mark.integration

async def test_logout_with_valid_token(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.post("/auth/logout")
    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully"

    response = await authorized_client_rbac_manager.get("/users/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Token has been revoked"
    
async def test_logout_with_invalid_token(authorized_client_rbac_manager):
    authorized_client_rbac_manager.headers["Authorization"] = "Bearer invalid_token"
    response = await authorized_client_rbac_manager.post("/auth/logout")
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"

async def test_access_api_after_expired_token(authorized_client_rbac_manager):
    response = await authorized_client_rbac_manager.get("/users/me")
    user = response.json()
    # need to create a token that expired in 1 second
    token = jwt.encode(
        {
            "sub": str(user["id"]),
            "user_code": user["user_code"],
            "user_type": user["user_type"],
            "exp": datetime.now(UTC) - timedelta(seconds=1),
            "jti": str(uuid4()),
        },
        settings.SECRET_KEY.get_secret_value(),
        algorithm=settings.ALGORITHM
    )
    authorized_client_rbac_manager.headers["Authorization"] = f"Bearer {token}"
    response = await authorized_client_rbac_manager.get("/users/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"