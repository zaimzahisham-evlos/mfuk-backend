from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.pagination import PaginationParams, build_list_query, count_query, fetch_paginated
from app.core.utils import set_attributes
from app.db.session import include_deleted_execution_options
from app.rbac.helpers import active_effective_user_role_clause, effective_now_clause, to_role_permission_response, to_user_role_response
from app.rbac.models import *
from sqlalchemy import and_, or_, select
from sqlalchemy.exc import IntegrityError
from ..rbac.schema import *

class RbacRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    """Permissions"""
    async def get_permissions(
        self, 
        include_deleted: bool = False, 
        modules: list[str] | None = None,
        statuses: list[PermissionStatus] | None = None,
        pagination: PaginationParams | None = None,
    ) -> list[Permission]:
        query = build_list_query(
            Permission,
            statuses=statuses,
            status_column=Permission.status,
            search=pagination.search if pagination else None,
            search_columns=(Permission.permission_code, Permission.permission_name),
            order_by=(Permission.created_at.desc(), Permission.id.desc()),
        )

        if modules:
            query = query.where(Permission.module.in_(modules))

        return await fetch_paginated(self.db, query, include_deleted=include_deleted, pagination=pagination)

    async def count_permissions(
        self, 
        include_deleted: bool = False, 
        modules: list[str] | None = None,
        statuses: list[PermissionStatus] | None = None,
        search: str | None = None,
    ) -> int:
        query = build_list_query(
            Permission,
            statuses=statuses,
            status_column=Permission.status,
            search=search,
            search_columns=(Permission.permission_code, Permission.permission_name),
        )
        if modules:
            query = query.where(Permission.module.in_(modules))
        return await count_query(self.db, query, include_deleted=include_deleted)

    async def get_permission_by_id(self, permission_id: int) -> Permission | None:
        query = select(Permission).where(Permission.id == permission_id, Permission.status != PermissionStatus.DELETED)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_permission_by_code(self, permission_code: str) -> Permission | None:
        query = select(Permission).where(
            Permission.permission_code == permission_code, 
            Permission.status != PermissionStatus.DELETED
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def create_permission(self, permission: PermissionCreate) -> Permission:
        new_permission = Permission(**permission.model_dump(exclude_unset=True))
        self.db.add(new_permission)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise

        await self.db.refresh(new_permission)
        return new_permission

    async def update_permission(self, permission: Permission, permission_updates: PermissionUpdate) -> Permission:
        updated_permission = permission_updates.model_dump(exclude_unset=True)
        set_attributes(permission, updated_permission)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise

        await self.db.refresh(permission)
        return permission


    """"Roles"""
    async def get_roles(
        self, 
        include_deleted: bool = False,
        statuses: list[RoleStatus] | None = None,
        pagination: PaginationParams | None = None,
    ) -> list[Role]:
        query = build_list_query(
            Role,
            statuses=statuses,
            status_column=Role.status,
            search=pagination.search if pagination else None,
            search_columns=(Role.role_code, Role.role_name),
            order_by=(Role.created_at.desc(), Role.id.desc()),
        )
        return await fetch_paginated(self.db, query, include_deleted=include_deleted, pagination=pagination)

    async def count_roles(
        self, 
        include_deleted: bool = False, 
        statuses: list[RoleStatus] | None = None,
        search: str | None = None,
    ) -> int:
        query = build_list_query(
            Role,
            statuses=statuses,
            status_column=Role.status,
            search=search,
            search_columns=(Role.role_code, Role.role_name),
        )
        return await count_query(self.db, query, include_deleted=include_deleted)

    async def get_role_by_id(self, role_id: int) -> Role | None:
        query = select(Role).where(Role.id == role_id, Role.status != RoleStatus.DELETED)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_role_by_code(self, role_code: str) -> Role | None:
        query = select(Role).where(
            Role.role_code == role_code, 
            Role.status != RoleStatus.DELETED
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def create_role(self, role: RoleCreate) -> Role:
        new_role = Role(**role.model_dump(exclude_unset=True))
        self.db.add(new_role)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise

        await self.db.refresh(new_role)
        return new_role

    async def update_role(self, role: Role, role_updates: RoleUpdate) -> Role:
        updated_role = role_updates.model_dump(exclude_unset=True)
        set_attributes(role, updated_role)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise

        await self.db.refresh(role)
        return role


    """Role Permissions"""
    def _role_permission_load_options(self):
        return (
            selectinload(RolePermission.role),
            selectinload(RolePermission.permission),
        )

    async def get_role_permissions(
        self, role_id: int, 
        include_deleted: bool = False, 
        statuses: Sequence[RolePermissionStatus] | None = None
    ) -> list[RolePermission]:
        query = (
            select(RolePermission)
            .join(Permission, Permission.id == RolePermission.permission_id)
            .where(
                RolePermission.role_id == role_id,
                Permission.status != PermissionStatus.DELETED,
            )
            .options(*self._role_permission_load_options())
            .order_by(RolePermission.priority.asc(), RolePermission.id.asc())
        )

        if include_deleted:
            statuses = [RolePermissionStatus.DELETED] + list(statuses or [])

        if statuses:
            query = query.where(RolePermission.status.in_(statuses))

        result = await self.db.execute(query, execution_options=include_deleted_execution_options(include_deleted))
        return list(result.scalars().all())

    async def get_role_permission_by_id(self, role_permission_id: int) -> RolePermission | None:
        query = (
            select(RolePermission)
            .where(
                RolePermission.id == role_permission_id, 
                RolePermission.status != RolePermissionStatus.DELETED
            )
            .options(*self._role_permission_load_options())
        )
        result = await self.db.execute(query, execution_options=include_deleted_execution_options(True))
        return result.scalars().first()

    async def get_role_permission(
        self, role_id: int, 
        permission_id: int, 
        priority: int = 100, 
        status: RolePermissionStatus | None = None
    ) -> RolePermission | None:
        query = (
            select(RolePermission)
            .where(
                RolePermission.role_id == role_id, 
                RolePermission.permission_id == permission_id, 
                RolePermission.priority == priority,
                RolePermission.status != RolePermissionStatus.DELETED
            )
            .options(*self._role_permission_load_options())
        )
        if status:
            query = query.where(RolePermission.status == status)

        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_effective_role_permissions(self, role_id: int, permission_id: int) -> list[RolePermission]:
        query = select(RolePermission).where(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id,
            RolePermission.status == RolePermissionStatus.ACTIVE,
            *effective_now_clause(RolePermission)
        ).order_by(RolePermission.priority.asc(), RolePermission.id.asc())
        result = await self.db.execute(query)
        return list(result.scalars().all())
        
    async def get_role_permission_by_permission(self, permission_id: int) -> list[RolePermission]:
        query = (
            select(RolePermission)
            .where(
                RolePermission.permission_id == permission_id, 
                RolePermission.status != RolePermissionStatus.DELETED
            )
            .options(*self._role_permission_load_options())
        )
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def assign_permissions_to_role(self, permissions_to_role: AssignPermissionsToRole) -> AssignPermissionsToRoleResponse:
        new_role_permissions: list[RolePermission] = []
        outcomes: list[AssignPermissionsToRoleOutcome] = []
        seen_keys: set[tuple[int, int]] = set()
        for permission_to_role in permissions_to_role.role_permissions:
            key = (permission_to_role.permission_id, permission_to_role.priority)
            if key in seen_keys:
                outcomes.append(AssignPermissionsToRoleOutcome(
                    permission_id=permission_to_role.permission_id,
                    priority=permission_to_role.priority,
                    role_permission=None,
                    status="duplicate_entry",
                    message=f"Duplicate entry for permission_id={permission_to_role.permission_id} with priority {permission_to_role.priority}"
                ))
                continue
            seen_keys.add(key)

            if permission_to_role.status == RolePermissionStatus.DELETED:
                # By default API will return 422 error due to schema validation, so this is just an extra guardrail to ensure we don't assign deleted permissions to the role
                outcomes.append(AssignPermissionsToRoleOutcome(
                    permission_id=permission_to_role.permission_id,
                    priority=permission_to_role.priority,
                    role_permission=None,
                    status="assigned_deleted",
                    message=f"Cannot assign permission_id={permission_to_role.permission_id} with status DELETED"
                ))
                continue

            permission = await self.get_permission_by_id(permission_to_role.permission_id)
            if not permission:
                outcomes.append(AssignPermissionsToRoleOutcome(
                    permission_id=permission_to_role.permission_id,
                    priority=permission_to_role.priority,
                    role_permission=None,
                    status="not_found_permission",
                    message=f"Permission with ID {permission_to_role.permission_id} not found"
                ))
                continue

            role_permission = await self.get_role_permission(
                permissions_to_role.role_id, 
                permission_to_role.permission_id, 
                permission_to_role.priority,
            )

            if role_permission: # role permission already exists
                outcomes.append(AssignPermissionsToRoleOutcome(
                    permission_id=permission_to_role.permission_id,
                    priority=permission_to_role.priority,
                    role_permission=to_role_permission_response(role_permission),
                    status="already_assigned",
                    message=f"Role permission with role ID {permissions_to_role.role_id} and permission ID {permission_to_role.permission_id} with priority {permission_to_role.priority} already exists with status {role_permission.status}"
                ))
                continue

            new_role_permission = RolePermission(
                role_id = permissions_to_role.role_id,
                permission_id = permission_to_role.permission_id,
                status = permission_to_role.status,
                effect = permission_to_role.effect,
                priority = permission_to_role.priority,
                valid_from = permission_to_role.valid_from,
                valid_until = permission_to_role.valid_until,
                notes = permission_to_role.notes,
                created_by_id = permissions_to_role.created_by_id,
            )
            new_role_permissions.append(new_role_permission)
            

        self.db.add_all(new_role_permissions)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise
        
        for role_permission in new_role_permissions:
            await self.db.refresh(role_permission, attribute_names=["role", "permission"])
            outcomes.append(AssignPermissionsToRoleOutcome(
                role_permission=to_role_permission_response(role_permission),
                permission_id=role_permission.permission_id,
                priority=role_permission.priority,
                status="assigned",
                message=None
            ))

        return AssignPermissionsToRoleResponse(
            role_id=permissions_to_role.role_id,
            outcomes=outcomes,
            requested_count=len(permissions_to_role.role_permissions),
            assigned_count=len(new_role_permissions),
            revoked_count=0,
            skipped_count=len(permissions_to_role.role_permissions) - len(new_role_permissions)
        )

    async def revoke_permissions_from_role(self, permissions_to_role: RevokePermissionsFromRole) -> RevokePermissionsFromRoleResponse:
        role_permissions: list[RolePermission] = []
        outcomes: list[RevokePermissionsFromRoleOutcome] = []
        seen_keys: set[int] = set()
        for role_permission in permissions_to_role.role_permissions:
            if role_permission.role_permission_id in seen_keys:
                outcomes.append(RevokePermissionsFromRoleOutcome(
                    role_permission_id=role_permission.role_permission_id,
                    role_permission=None,
                    status="duplicate_entry",
                    message=f"Duplicate entry for role_permission_id={role_permission.role_permission_id}"
                ))
                continue
            seen_keys.add(role_permission.role_permission_id)

            existing_role_permission = await self.get_role_permission_by_id(role_permission.role_permission_id)
            if not existing_role_permission:
                outcomes.append(RevokePermissionsFromRoleOutcome(
                    role_permission_id=role_permission.role_permission_id,
                    role_permission=None,
                    status="not_found_role_permission",
                    message=f"Role permission with ID {role_permission.role_permission_id} not found"
                ))
                continue

            set_attributes(existing_role_permission, {
                "status": RolePermissionStatus.DELETED,
                "notes": role_permission.notes or existing_role_permission.notes,
                "deleted_at": permissions_to_role.deleted_at,
                "deleted_by_id": permissions_to_role.deleted_by_id,
                "updated_by_id": permissions_to_role.updated_by_id,
            })
            self.db.add(existing_role_permission)
            role_permissions.append(existing_role_permission)

        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise

        for role_permission in role_permissions:
            await self.db.refresh(role_permission, attribute_names=["role", "permission"])
            outcomes.append(RevokePermissionsFromRoleOutcome(
                role_permission_id=role_permission.id,
                role_permission=to_role_permission_response(role_permission),
                status="revoked",
                message=None
            ))

        return RevokePermissionsFromRoleResponse(
            role_id=permissions_to_role.role_id,
            outcomes=outcomes,
            requested_count=len(permissions_to_role.role_permissions),
            assigned_count=0,
            revoked_count=len(role_permissions),
            skipped_count=len(permissions_to_role.role_permissions) - len(role_permissions)
        )

    async def update_role_permission(self, role_permission: RolePermission, role_permission_updates: RolePermissionUpdate) -> RolePermission:
        updated_role_permission = role_permission_updates.model_dump(exclude_unset=True)
        set_attributes(role_permission, updated_role_permission)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise

        await self.db.refresh(role_permission, attribute_names=["role", "permission"])
        return role_permission

    """User Roles"""
    def _user_role_load_options(self):
        return (
            selectinload(UserRole.role),
            selectinload(UserRole.user),
        )
        
    async def get_user_roles(
        self, 
        user_id: int, 
        include_deleted: bool = False, 
        statuses: Sequence[UserRoleStatus] | None = None,
        include_active_effective: bool = True,
    ) -> list[UserRole]:
        """
        Get User Roles by User ID with statuses filter. If statuses is None, all statuses are returned except DELETED.
        if include_active_effective is True (default) and statuses includes ACTIVE, 
            then the active roles returned are only the active roles that are effective (valid window is effective).
        else, all statuses in statuses are returned.
        """
        query = (
            select(UserRole)
            .join(Role, Role.id == UserRole.role_id)
            .where(
                UserRole.user_id == user_id,
                Role.status != RoleStatus.DELETED,
            )
            .options(*self._user_role_load_options())
        )
        if statuses:
            if UserRoleStatus.ACTIVE in statuses and include_active_effective:
                query = active_effective_user_role_clause(query, statuses)
            else:
                query = query.where(UserRole.status.in_(statuses))

        result = await self.db.execute(query, execution_options=include_deleted_execution_options(include_deleted))
        return list(result.scalars().all())

    async def get_user_role_by_id(self, user_role_id: int) -> UserRole | None:
        query = select(UserRole).where(
            UserRole.id == user_role_id, 
            UserRole.status != UserRoleStatus.DELETED
        ).options(*self._user_role_load_options())
        result = await self.db.execute(query, execution_options=include_deleted_execution_options(True))
        return result.scalars().first()

    async def get_user_role(
        self, user_id: int, 
        role_id: int, 
        status: UserRoleStatus | None = None,
        exclude_revoked: bool = True
    ) -> UserRole | None:
        """
        Get User Role by User ID and Role ID with statuses filter.
        If status is None, all statuses are returned except DELETED. 
        If exclude_revoked is True, then the role with the status is returned.
        If status is ACTIVE, then the active role returned is only the active role that is effective (valid window is effective).
        else, the role with the status is returned.
        """
        query = (
            select(UserRole)
            .where(
                UserRole.user_id == user_id, 
                UserRole.role_id == role_id, 
                UserRole.status != UserRoleStatus.DELETED
            )
            .options(*self._user_role_load_options())
            .order_by(UserRole.created_at.desc(), UserRole.id.desc())
        )
        
        if status:
            query = query.where(UserRole.status == status)

        if exclude_revoked and status != UserRoleStatus.REVOKED:
            query = query.where(UserRole.status != UserRoleStatus.REVOKED)

        result = await self.db.execute(query, execution_options=include_deleted_execution_options(True))
        return result.scalars().first()

    async def get_effective_user_roles(self, user_id: int) -> list[UserRole]:
        query = (
            select(UserRole)
            .join(Role, Role.id == UserRole.role_id)
            .where(
                UserRole.user_id == user_id, 
                UserRole.status == UserRoleStatus.ACTIVE, 
                Role.status == RoleStatus.ACTIVE,
                *effective_now_clause(UserRole)
            )
            .order_by(UserRole.created_at.desc(), UserRole.id.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def assign_roles_to_user(self, roles_to_user: AssignRolesToUser) -> AssignRolesToUserResponse:
        new_user_roles: list[UserRole] = []
        outcomes: list[AssignRolesToUserOutcome] = []
        seen_role_ids: set[int] = set()

        for user_role in roles_to_user.user_roles:
            if user_role.role_id in seen_role_ids:
                outcomes.append(AssignRolesToUserOutcome(
                    role_id=user_role.role_id,
                    user_role=None,
                    status="duplicate_role",
                    message=f"Duplicate role_id={user_role.role_id} in request payload"
                ))
                continue
            seen_role_ids.add(user_role.role_id)
            
            if user_role.status == UserRoleStatus.DELETED:
                outcomes.append(AssignRolesToUserOutcome(
                    role_id=user_role.role_id,
                    user_role=None,
                    status="assigned_deleted",
                    message=f"Cannot assign role_id={user_role.role_id} with status DELETED"
                ))
                continue

            role = await self.get_role_by_id(user_role.role_id)
            if not role:
                outcomes.append(AssignRolesToUserOutcome(
                    role_id=user_role.role_id,
                    user_role=None,
                    status="not_found_role",
                    message=f"Role with ID {user_role.role_id} not found"
                ))
                continue

            existing_user_role = await self.get_user_role(
                roles_to_user.user_id, 
                user_role.role_id,
            )
            if existing_user_role: # user role already exists
                outcomes.append(AssignRolesToUserOutcome(
                    role_id=user_role.role_id,
                    user_role=to_user_role_response(existing_user_role),
                    status="already_assigned",
                    message=f"User role with user ID {roles_to_user.user_id} and role ID {user_role.role_id} already exists with status {existing_user_role.status.value}"
                ))
                continue

            new_user_role = UserRole(
                user_id=roles_to_user.user_id,
                role_id=user_role.role_id,
                status=user_role.status or UserRoleStatus.ACTIVE,
                valid_from=user_role.valid_from,
                valid_until=user_role.valid_until,
                reason=user_role.reason,
                created_by_id=roles_to_user.created_by_id,
                assigned_by_id=roles_to_user.assigned_by_id,
                assigned_at=roles_to_user.assigned_at,
            )
            new_user_roles.append(new_user_role)

        self.db.add_all(new_user_roles)

        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise

        for user_role in new_user_roles:
            await self.db.refresh(user_role, attribute_names=["user", "role"])
            outcomes.append(AssignRolesToUserOutcome(
                role_id=user_role.role_id,
                user_role=to_user_role_response(user_role),
                status="assigned",
                message=None
            ))
        
        return AssignRolesToUserResponse(
            user_id=roles_to_user.user_id,
            outcomes=outcomes,
            requested_count=len(roles_to_user.user_roles),
            assigned_count=len(new_user_roles),
            revoked_count=0,
            skipped_count=len(roles_to_user.user_roles) - len(new_user_roles)
        )

    async def revoke_roles_from_user(self, roles_to_user: RevokeRolesFromUser) -> RevokeRolesFromUserResponse:
        user_roles: list[UserRole] = []
        outcomes: list[RevokeRolesFromUserOutcome] = []
        seen_role_ids: set[int] = set()
        for user_role in roles_to_user.user_roles:
            if user_role.user_role_id in seen_role_ids:
                outcomes.append(RevokeRolesFromUserOutcome(
                    user_role_id=user_role.user_role_id,
                    user_role=None,
                    status="duplicate_entry",
                    message=f"Duplicate user_role_id={user_role.user_role_id} in request payload"
                ))
                continue
            seen_role_ids.add(user_role.user_role_id)


            existing_user_role = await self.get_user_role_by_id(
                user_role.user_role_id
            )
            if not existing_user_role:
                outcomes.append(RevokeRolesFromUserOutcome(
                    user_role_id=user_role.user_role_id,
                    user_role=None,
                    status="not_found_user_role",
                    message=f"User role with ID {user_role.user_role_id} not found"
                ))
                continue

            if existing_user_role.status == UserRoleStatus.REVOKED:
                outcomes.append(RevokeRolesFromUserOutcome(
                    user_role_id=user_role.user_role_id,
                    user_role=None,
                    status="already_revoked",
                    message=f"User role with ID {user_role.user_role_id} already revoked"
                ))
                continue

            set_attributes(existing_user_role, {
                "status": UserRoleStatus.REVOKED,
                "revoked_at": roles_to_user.revoked_at,
                "revoked_by_id": roles_to_user.revoked_by_id,
                "updated_by_id": roles_to_user.updated_by_id,
                "reason": user_role.reason,
            })
            self.db.add(existing_user_role)
            user_roles.append(existing_user_role)

        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise

        for user_role in user_roles:
            await self.db.refresh(user_role, attribute_names=["user", "role"])
            outcomes.append(RevokeRolesFromUserOutcome(
                user_role_id=user_role.id,
                user_role=to_user_role_response(user_role),
                status="revoked",
                message=None
            ))

        return RevokeRolesFromUserResponse(
            user_id=roles_to_user.user_id,
            outcomes=outcomes,
            requested_count=len(roles_to_user.user_roles),
            assigned_count=0,
            revoked_count=len(user_roles),
            skipped_count=len(roles_to_user.user_roles) - len(user_roles)
        )

    async def update_user_role(self, user_role: UserRole, user_role_updates: UserRoleUpdate | UserRoleDelete) -> UserRole:
        updated_user_role = user_role_updates.model_dump(exclude_unset=True)
        set_attributes(user_role, updated_user_role)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise

        await self.db.refresh(user_role, attribute_names=["user", "role"])
        return user_role

    """User Permissions"""
    async def get_effective_permission_rules_for_user(
        self, user_id: int, permission_code: str
    ) -> list[RolePermission]:
        """
        Get effective role-permission rules for a user based on permission code
        """
        query = (
            select(RolePermission)
            .join(
                UserRole, 
                and_(
                    UserRole.role_id == RolePermission.role_id,
                    UserRole.user_id == user_id
                )
            )
            .join(Role, Role.id == UserRole.role_id)
            .join(Permission, Permission.id == RolePermission.permission_id)
            .where(
                Permission.permission_code == permission_code,
                Permission.status == PermissionStatus.ACTIVE,
                Role.status == RoleStatus.ACTIVE,
                UserRole.status == UserRoleStatus.ACTIVE,
                RolePermission.status == RolePermissionStatus.ACTIVE,
                *effective_now_clause(RolePermission),
                *effective_now_clause(UserRole),
            )
            .order_by(RolePermission.priority.asc(), RolePermission.id.asc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def user_has_role_code(self, user_id: int, role_code: str) -> bool:
        query = (
            select(UserRole)
            .join(Role, Role.id == UserRole.role_id)
            .where(
                UserRole.user_id == user_id,
                Role.role_code == role_code,
                UserRole.status == UserRoleStatus.ACTIVE,
                Role.status == RoleStatus.ACTIVE,
            )
            .order_by(UserRole.created_at.desc(), UserRole.id.desc())
        )
        result = await self.db.execute(query)
        return result.scalars().first() is not None