from fastapi import Depends
from typing import Annotated

from app.core.exceptions import ForbiddenError
from app.rbac.services import RbacService
from ..user.schema import UserResponse
from ..db.session import get_db
from ..auth.services import AuthenticationService, oauth2_scheme
from sqlalchemy.ext.asyncio import AsyncSession

async def get_current_user_from_token(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    return await AuthenticationService(db).user_from_token(token, refresh=False)

async def get_current_user_from_token_refresh(
    token: Annotated[str, Depends(oauth2_scheme)], 
    db: Annotated[AsyncSession, Depends(get_db)]
) -> UserResponse:
    return await AuthenticationService(db).user_from_token(token, refresh=True)

CurrentUser = Annotated[UserResponse, Depends(get_current_user_from_token)]

CurrentUserFromTokenRefresh = Annotated[UserResponse, Depends(get_current_user_from_token_refresh)]

def require_permission(permission_code: str):
    async def permission_dependency(
        current_user: CurrentUser,
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> UserResponse:
        allowed = await RbacService(db).has_permission(current_user.id, permission_code)
        if not allowed:
            raise ForbiddenError(f"User does not have permission to access {permission_code}")
        return current_user
    
    return permission_dependency