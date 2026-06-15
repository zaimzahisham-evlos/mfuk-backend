import logging
from typing import Sequence
from sqlalchemy.exc import IntegrityError
from app.core.pagination import PaginatedResponse, PaginationParams, to_paginated_response
from app.core.utils import utcnow
from app.user.helpers import to_user_response, validate_auth_on_create, validate_auth_on_update
from ..user.models import UserStatus
from ..user.repository import UserRepository
from ..user.schema import UserCreate, UserResponse, UserRoleCode, UserUpdate
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.exceptions import BadRequestError, NotFoundError

class UserService:
    def __init__(self, db: AsyncSession):
        self.repo = UserRepository(db)
        self.db = db

    async def get_users(
        self, 
        include_deleted: bool = False, 
        statuses: Sequence[UserStatus] | None = None, 
        pagination: PaginationParams | None = None
    ) -> PaginatedResponse[UserResponse]:
        total = await self.repo.count_users(include_deleted, statuses, pagination.search if pagination else None)
        users = await self.repo.get_users(include_deleted, statuses, pagination)
        items = [to_user_response(user) for user in users]
        return to_paginated_response(items, total, pagination)

    async def get_user_by_id(self, user_id: int, status: UserStatus | None = None) -> UserResponse:
        user = await self.repo.get_user_by_id(user_id, status)
        if not user:
            raise NotFoundError(f"User with ID {user_id} not found")
        return to_user_response(user)

    async def get_user_by_user_code(self, user_code: str, status: UserStatus | None = None) -> UserResponse:
        user_code = user_code.strip().upper()
        user = await self.repo.get_user_by_user_code(user_code, status)
        if not user:
            raise NotFoundError(f"User with user code {user_code} not found")

        return to_user_response(user)


    async def create_user(self, user: UserCreate) -> UserResponse:
        if user.status == UserStatus.DELETED:
            raise BadRequestError("Cannot create a user with status Deleted")
        existing_user = await self.repo.get_user_by_user_code(user.user_code.strip().upper())
        if existing_user:
            raise BadRequestError(f"User with user code {user.user_code} already exists")

        validate_auth_on_create(user)

        try:
            new_user = await self.repo.create_user(user)
            new_user = to_user_response(new_user)
                
        except IntegrityError as e:
            logging.error(f"Error creating user: {e}")
            raise BadRequestError(f"Invalid user payload or conflicting user data")
        
        return new_user

    async def update_user(self, user_code: str, user_updates: UserUpdate) -> UserResponse:
        user_code = user_code.strip().upper()
        existing_user = await self.repo.get_user_by_user_code(user_code)
        if not existing_user:
            raise NotFoundError(f"User with user code {user_code} not found")

        if user_updates.status == UserStatus.DELETED:
            user_updates = user_updates.model_copy(update={
                "deleted_by_id": user_updates.updated_by_id,
                "deleted_at": utcnow(),
                "password": None
            })

        if user_updates.status == UserStatus.DELETED and "password" not in user_updates.model_fields_set:
            user_updates = user_updates.model_copy(update={"password": None})

        validate_auth_on_update(existing_user, user_updates)

        try:
            updated_user = await self.repo.update_user(existing_user, user_updates)
            updated_user = to_user_response(updated_user)
        except IntegrityError as e:
            logging.error(f"Error updating user: {e}")
            raise BadRequestError(f"Invalid user payload or conflicting user data")

        return updated_user

    async def delete_user(self, user_code: str, deleted_by_id: int) -> None:
        user_code = user_code.strip().upper()
        user = await self.repo.get_user_by_user_code(user_code)
        if not user:
            raise NotFoundError(f"User with user code {user_code} not found")

        if user.status == UserStatus.DELETED:
            raise BadRequestError(f"User with user code {user_code} is already deleted")

        user_updates = UserUpdate(
            deleted_by_id=deleted_by_id, 
            deleted_at=utcnow(), 
            status=UserStatus.DELETED,
            updated_by_id=deleted_by_id,
            password=None,
        )
        try:
            await self.repo.update_user(user, user_updates)
        except IntegrityError as e:
            logging.error(f"Error deleting user: {e}")
            raise BadRequestError(f"Invalid user payload or conflicting user data")
    