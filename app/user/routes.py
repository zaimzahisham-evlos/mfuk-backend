from fastapi import APIRouter, Depends, Query, status
from app.core.pagination import PaginatedResponse, PaginationParams
from app.core.utils import utcnow
from app.rbac.services import RbacService
from app.user.models import UserStatus
import logging
from ..user.services import UserService
from ..user.schema import UserCreateRequest, UserResponse, UserCreate, UserUpdate, USER404, USER400, USERPATCHDELETE, UserUpdateRequest
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, Sequence
from ..db.session import get_db
from ..core.exceptions import ForbiddenError
from ..auth.dependencies import CurrentUser, require_permission
from ..auth.schema import INVALID_OR_EXPIRED_TOKEN

router = APIRouter()

@router.get("/", response_model=PaginatedResponse[UserResponse])
# @limiter.limit("100/minute")
async def get_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[UserResponse, Depends(require_permission("USER_VIEW"))],
    pagination: Annotated[PaginationParams, Depends()],
    include_deleted: bool = False,
    statuses: Annotated[Sequence[UserStatus] | None, Query()] = None,
):
    logging.info("Getting users")
    return await UserService(db).get_users(include_deleted, statuses, pagination)


@router.get("/me", response_model=UserResponse, responses={**INVALID_OR_EXPIRED_TOKEN})
async def get_me(user: CurrentUser):
    """Get current authenticated user"""
    logging.info(f"Getting current authenticated user")
    return user

@router.get("/{user_code}", response_model=UserResponse, responses={**USER404})
async def get_user(
    user_code: str, db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[UserResponse, Depends(require_permission("USER_VIEW"))]
):
    logging.info(f"Getting user {user_code}")
    return await UserService(db).get_user_by_user_code(user_code)

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED, responses={**USER400})
async def create_user(
    user: UserCreateRequest, db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[UserResponse, Depends(require_permission("USER_CREATE"))]
):
    logging.info(f"Creating user {user.user_code}")
    user_create = UserCreate(
        **user.model_dump(exclude_unset=True),
        created_by_id=current_user.id
    )
    return await UserService(db).create_user(user_create)

@router.patch("/{user_code}", response_model=UserResponse, responses={**USERPATCHDELETE})
async def update_user(
    user_code: str, user: UserUpdateRequest, 
    db: Annotated[AsyncSession, Depends(get_db)], 
    current_user: CurrentUser
):
    logging.info(f"Updating user {user_code}")
    # only allow update if user is updating their own user or has permission to update other users
    has_permission = await RbacService(db).has_permission(current_user.id, "USER_UPDATE")
    allowed_to_update = current_user.user_code == user_code.strip().upper() or has_permission
    if not allowed_to_update:
        raise ForbiddenError(detail="You are not allowed to update this user")
    
    user_updates = UserUpdate(
        **user.model_dump(exclude_unset=True),
        updated_by_id=current_user.id
    )

    return await UserService(db).update_user(user_code, user_updates)

@router.delete("/{user_code}", status_code=status.HTTP_204_NO_CONTENT, responses={**USERPATCHDELETE})
async def delete_user(
    user_code: str, db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[UserResponse, Depends(require_permission("USER_DELETE"))]
):
    logging.info(f"Deleting user {user_code}")
    return await UserService(db).delete_user(user_code, current_user.id)