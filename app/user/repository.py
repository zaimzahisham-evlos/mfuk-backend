from typing import Sequence
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload, with_loader_criteria
from app.auth.services import AuthenticationService
from app.core.pagination import PaginationParams, build_list_query, count_query, fetch_paginated
from app.core.utils import set_attributes
from app.user.schema import UserCreate, UserUpdate
from ..user.models import User, UserStatus
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _effective_role_load_options(self):
        from app.rbac.models import UserRole, Role, UserRoleStatus, RoleStatus
        from app.rbac.helpers import effective_now_clause
        return (
            # load user.roles_assigned and user_role.role in one IN-query
            selectinload(User.roles_assigned).selectinload(UserRole.role),
            # filter loaded UserRole rows to "active + effective now"
            with_loader_criteria(
                UserRole,
                and_(
                    UserRole.status == UserRoleStatus.ACTIVE,
                    *effective_now_clause(UserRole),
                ),
                include_aliases=True,
            ),

            # filter loaded Role rows to "active"
            with_loader_criteria(
                Role,
                Role.status == RoleStatus.ACTIVE,
                include_aliases=True,
            ),
        )

    async def get_users(
        self, 
        include_deleted: bool = False,
        statuses: Sequence[UserStatus] | None = None,
        pagination: PaginationParams | None = None
    ) -> list[User]:
        query = build_list_query(
            User,
            statuses=statuses,
            status_column=User.status,
            search=pagination.search if pagination else None,
            search_columns=(User.user_code, User.full_name),
            order_by=(User.created_at.desc(), User.id.desc()),
        )
        query = query.options(*self._effective_role_load_options())
        return await fetch_paginated(self.db, query, include_deleted=include_deleted, pagination=pagination)

    async def count_users(
        self, 
        include_deleted: bool = False, 
        statuses: Sequence[UserStatus] | None = None, 
        search: str | None = None
    ) -> int:
        query = build_list_query(
            User,
            statuses=statuses,
            status_column=User.status,
            search=search,
            search_columns=(User.user_code, User.full_name),
        )
        return await count_query(self.db, query, include_deleted=include_deleted)

    async def get_user_by_id(self, user_id: int, status: UserStatus | None = None) -> User | None:
        query = select(User).where(User.id == user_id, User.status != UserStatus.DELETED)
        if status:
            query = query.where(User.status == status)
        query = query.options(*self._effective_role_load_options())
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_user_by_user_code(self, user_code: str, status: UserStatus | None = None) -> User | None:
        query = select(User).where(User.user_code == user_code, User.status != UserStatus.DELETED)
        if status:
            query = query.where(User.status == status)
        query = query.options(*self._effective_role_load_options())
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_effective_user_role_codes(self, user_id: int) -> list[dict]:
        from app.rbac.models import Role, UserRole, UserRoleStatus, RoleStatus
        from app.rbac.helpers import effective_now_clause
        query = (
            select(Role)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(
                UserRole.user_id == user_id,
                UserRole.status == UserRoleStatus.ACTIVE,
                Role.status == RoleStatus.ACTIVE,
                *effective_now_clause(UserRole)
            )
            .order_by(Role.created_at.desc(), Role.id.desc())
        )
        result = await self.db.execute(query)
        return [{"id": role.id, "role_code": role.role_code} for role in result.scalars().all()]

    async def create_user(self, user: UserCreate) -> User:
        new_user = User(**user.model_dump(exclude_unset=True, exclude={"password"}))

        if user.password is not None:
            new_user.password_hash= AuthenticationService.hash_password(user.password)

        self.db.add(new_user)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise

        await self.db.refresh(new_user, ["roles_assigned"])
        return new_user

    async def update_user(self, user: User, user_updates: UserUpdate) -> User:
        updated_user = user_updates.model_dump(exclude_unset=True, exclude={"password"})

        if "password" in user_updates.model_fields_set:
            if user_updates.password is None:
                updated_user["password_hash"] = None
            else:
                updated_user["password_hash"] = AuthenticationService.hash_password(user_updates.password)   

        set_attributes(user, updated_user)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise

        await self.db.refresh(user, ["roles_assigned"])
        return user