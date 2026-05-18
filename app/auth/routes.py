from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from ..auth.schema import Token, INVALID_CREDENTIALS, INVALID_OR_EXPIRED_TOKEN, LoginRequest
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.session import get_db
from ..auth.services import AuthenticationService, oauth2_scheme
import logging
from ..auth.dependencies import CurrentUserFromTokenRefresh

router = APIRouter()

@router.post("/login", response_model=Token, responses={**INVALID_CREDENTIALS})
async def login(
    payload: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Login a user"""
    logging.info(f"Logging in user {payload.user_code}")
    user_token = await AuthenticationService(db).login_user_by_user_code(payload.user_code, payload.password)
    return user_token

@router.post("/refresh", response_model=Token, responses={**INVALID_OR_EXPIRED_TOKEN})
async def refresh(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: CurrentUserFromTokenRefresh,
    token: Annotated[str, Depends(oauth2_scheme)]
):
    """Refresh a token"""
    logging.info(f"Refreshing token for user {user.id}")
    user_token = await AuthenticationService(db).refresh_token(token, user)
    return user_token

@router.post("/logout", responses={**INVALID_OR_EXPIRED_TOKEN})
async def logout(
    db: Annotated[AsyncSession, Depends(get_db)],
    token: Annotated[str, Depends(oauth2_scheme)]
):
    """Logout a user"""
    await AuthenticationService(db).logout(token)
    return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "Logged out successfully"})