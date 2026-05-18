import logging
from typing import Sequence
from sqlalchemy.exc import IntegrityError
from app.core.utils import utcnow
from app.rbac.helpers import to_role_permission_response, to_user_role_response
from app.rbac.repository import RbacRepository
from app.rbac.schema import *
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.exceptions import BadRequestError, NotFoundError

class RbacService:
    def __init__(self, db: AsyncSession):
        from app.user.services import UserService
        self.repo = RbacRepository(db)
        self.user_service = UserService(db)

    """Permissions"""
    async def get_permissions(self, include_deleted: bool = False, modules: list[str] | None = None) -> list[PermissionResponse]:
        if modules:
            modules = [module.strip().title() for module in modules]
        permissions = await self.repo.get_permissions(include_deleted, modules)
        return [PermissionResponse.model_validate(permission) for permission in permissions]

    async def get_permission_by_code(self, permission_code: str) -> PermissionResponse:
        permission_code = permission_code.strip().upper()
        permission = await self.repo.get_permission_by_code(permission_code)
        if not permission:
            raise NotFoundError(f"Permission with code {permission_code} not found")
        return PermissionResponse.model_validate(permission)

    async def get_permission_by_id(self, permission_id: int) -> PermissionResponse:
        permission = await self.repo.get_permission_by_id(permission_id)
        if not permission:
            raise NotFoundError(f"Permission with ID {permission_id} not found")
        return PermissionResponse.model_validate(permission)

    async def create_permission(self, permission: PermissionCreate) -> PermissionResponse:
        if permission.status == PermissionStatus.DELETED:
            raise BadRequestError("Cannot create a permission with status Deleted")

        existing_permission = await self.repo.get_permission_by_code(permission.permission_code.strip().upper())
        if existing_permission:
            raise BadRequestError(f"Permission with code {permission.permission_code} already exists")
        
        try:
            new_permission = await self.repo.create_permission(permission)
        except IntegrityError as e:
            logging.error(f"Error creating permission: {e}")
            raise BadRequestError(f"Invalid permission payload or conflicting permission data")
        
        return PermissionResponse.model_validate(new_permission)

    async def update_permission(self, permission_code: str, permission_updates: PermissionUpdate) -> PermissionResponse:
        permission_code = permission_code.strip().upper()
        existing_permission = await self.repo.get_permission_by_code(permission_code)
        if not existing_permission:
            raise NotFoundError(f"Permission with code {permission_code} not found")

        if existing_permission.is_system_permission:
            raise BadRequestError("Cannot update a system permission")

        if permission_updates.status == PermissionStatus.DELETED:
            permission_updates = permission_updates.model_copy(update={
                "deleted_by_id": permission_updates.updated_by_id,
                "deleted_at": utcnow(),
            })

        try:
            updated_permission = await self.repo.update_permission(existing_permission, permission_updates)
        except IntegrityError as e:
            logging.error(f"Error updating permission: {e}")
            raise BadRequestError(f"Invalid permission payload or conflicting permission data")
        
        return PermissionResponse.model_validate(updated_permission)

    async def delete_permission(self, permission_code: str, deleted_by_id: int) -> None:
        permission_code = permission_code.strip().upper()
        existing_permission = await self.repo.get_permission_by_code(permission_code)
        if not existing_permission:
            raise NotFoundError(f"Permission with code {permission_code} not found")

        if existing_permission.status == PermissionStatus.DELETED:
            raise BadRequestError(f"Permission with code {permission_code} is already deleted")

        if existing_permission.is_system_permission:
            raise BadRequestError("Cannot delete a system permission")

        permission_updates = PermissionUpdate(
            deleted_by_id=deleted_by_id,
            deleted_at=utcnow(),
            status=PermissionStatus.DELETED,
            updated_by_id=deleted_by_id,
        )

        try:
            await self.repo.update_permission(existing_permission, permission_updates)
        except IntegrityError as e:
            logging.error(f"Error deleting permission: {e}")
            raise BadRequestError(f"Invalid permission payload or conflicting permission data")
    
    """Roles"""
    async def get_roles(self, include_deleted: bool = False) -> list[RoleResponse]:
        roles = await self.repo.get_roles(include_deleted)
        return [RoleResponse.model_validate(role) for role in roles]

    async def get_role_by_code(self, role_code: str) -> RoleResponse:
        role_code = role_code.strip().upper()
        role = await self.repo.get_role_by_code(role_code)
        if not role:
            raise NotFoundError(f"Role with code {role_code} not found")
        return RoleResponse.model_validate(role)

    async def get_role_by_id(self, role_id: int) -> RoleResponse:
        role = await self.repo.get_role_by_id(role_id)
        if not role:
            raise NotFoundError(f"Role with ID {role_id} not found")
        return RoleResponse.model_validate(role)

    async def create_role(self, role: RoleCreate) -> RoleResponse:
        if role.status == RoleStatus.DELETED:
            raise BadRequestError("Cannot create a role with status Deleted")

        existing_role = await self.repo.get_role_by_code(role.role_code.strip().upper())
        if existing_role:
            raise BadRequestError(f"Role with code {role.role_code} already exists")
        
        try:
            new_role = await self.repo.create_role(role)
        except IntegrityError as e:
            logging.error(f"Error creating role: {e}")
            raise BadRequestError(f"Invalid role payload or conflicting role data")
        
        return RoleResponse.model_validate(new_role)

    async def update_role(self, role_code: str, role_updates: RoleUpdate) -> RoleResponse:
        role_code = role_code.strip().upper()
        existing_role = await self.repo.get_role_by_code(role_code)
        if not existing_role:
            raise NotFoundError(f"Role with code {role_code} not found")

        if existing_role.is_system_role:
            raise BadRequestError("Cannot update a system role")
        
        if role_updates.status == RoleStatus.DELETED:
            role_updates = role_updates.model_copy(update={
                "deleted_by_id": role_updates.updated_by_id,
                "deleted_at": utcnow(),
            })

        try:
            updated_role = await self.repo.update_role(existing_role, role_updates)
        except IntegrityError as e:
            logging.error(f"Error updating role: {e}")
            raise BadRequestError(f"Invalid role payload or conflicting role data")
        
        return RoleResponse.model_validate(updated_role)

    async def delete_role(self, role_code: str, deleted_by_id: int) -> None:
        role_code = role_code.strip().upper()
        existing_role = await self.repo.get_role_by_code(role_code)
        if not existing_role:
            raise NotFoundError(f"Role with code {role_code} not found")

        if existing_role.status == RoleStatus.DELETED:
            raise BadRequestError(f"Role with code {role_code} is already deleted")

        if existing_role.is_system_role:
            raise BadRequestError("Cannot delete a system role")

        role_updates = RoleUpdate(
            deleted_by_id=deleted_by_id,
            deleted_at=utcnow(),
            status=RoleStatus.DELETED,
            updated_by_id=deleted_by_id,
        )

        try:
            await self.repo.update_role(existing_role, role_updates)
        except IntegrityError as e:
            logging.error(f"Error deleting role: {e}")
            raise BadRequestError(f"Invalid role payload or conflicting role data")

    
    """Role Permissions"""
    async def get_role_permissions(
        self, role_id: int, 
        include_deleted: bool = False, 
        statuses: Sequence[RolePermissionStatus] | None = None
    ) -> list[RolePermissionResponse]:
        await self.get_role_by_id(role_id)
        role_permissions = await self.repo.get_role_permissions(role_id, include_deleted, statuses)
        return [to_role_permission_response(role_permission) for role_permission in role_permissions]

    async def get_role_permission_by_id(self, role_permission_id: int) -> RolePermissionResponse:
        role_permission = await self.repo.get_role_permission_by_id(role_permission_id)
        if not role_permission:
            raise NotFoundError(f"Role permission with ID {role_permission_id} not found")
        return to_role_permission_response(role_permission)

    async def get_role_permission(
        self, role_id: int, 
        permission_id: int, 
        priority: int = 100, 
        status: RolePermissionStatus | None = None
    ) -> RolePermissionResponse:
        role_permission = await self.repo.get_role_permission(role_id, permission_id, priority, status)
        if not role_permission:
            raise NotFoundError(f"Role permission with role ID {role_id} and permission ID {permission_id} with priority {priority} not found")
        return to_role_permission_response(role_permission)

    async def get_role_permission_by_permission(self, permission_id: int) -> list[RolePermissionResponse]:
        role_permissions = await self.repo.get_role_permission_by_permission(permission_id)
        return [to_role_permission_response(role_permission) for role_permission in role_permissions]

    async def assign_permissions_to_role(self, permissions_to_role: AssignPermissionsToRole) -> AssignPermissionsToRoleResponse:
        await self.get_role_by_id(permissions_to_role.role_id)
        try:
            assigned_role_permissions = await self.repo.assign_permissions_to_role(permissions_to_role)
        except IntegrityError as e:
            logging.error(f"Error assigning permissions to role: {e}")
            raise BadRequestError(f"Invalid permissions to role payload or conflicting permissions to role data")
        return assigned_role_permissions

    async def revoke_permissions_from_role(self, role_permissions: RevokePermissionsFromRole) -> RevokePermissionsFromRoleResponse:
        await self.get_role_by_id(role_permissions.role_id)
        try:
            revoked_role_permissions = await self.repo.revoke_permissions_from_role(role_permissions)
        except IntegrityError as e:
            logging.error(f"Error revoking permissions from role: {e}")
            raise BadRequestError(f"Invalid permissions to role payload or conflicting permissions to role data")
        return revoked_role_permissions

    async def update_role_permission(self, role_permission_id: int, role_permission_updates: RolePermissionUpdate) -> RolePermissionResponse:
        role_permission = await self.repo.get_role_permission_by_id(role_permission_id)
        if not role_permission:
            raise NotFoundError(f"Role permission with ID {role_permission_id} not found")

        try:
            updated_role_permission = await self.repo.update_role_permission(role_permission, role_permission_updates)
        except IntegrityError as e:
            logging.error(f"Error updating role permission: {e}")
            raise BadRequestError(f"Invalid role permission payload or conflicting role permission data")
        
        return to_role_permission_response(updated_role_permission)

    async def resolve_role_permission_effect(self, role_id: int, permission_id: int) -> RolePermissionEffect:
        await self.get_role_by_id(role_id)
        await self.get_permission_by_id(permission_id)
        effective_role_permissions = await self.repo.get_effective_role_permissions(role_id, permission_id)

        # first matching rule wins (sorted by priority asc). Default is DENY.
        if not effective_role_permissions:
            return RolePermissionEffect.DENY

        return effective_role_permissions[0].effect


    """User Roles"""
    async def get_user_roles(
        self, user_id: int, 
        include_deleted: bool = False,
        statuses: Sequence[UserRoleStatus] | None = None,
        include_active_effective: bool = True,
    ) -> list[UserRoleResponse]:
        await self.user_service.get_user_by_id(user_id)
        user_roles = await self.repo.get_user_roles(user_id, include_deleted, statuses, include_active_effective)
        return [to_user_role_response(user_role) for user_role in user_roles]

    async def get_user_role_by_id(self, user_role_id: int) -> UserRoleResponse:
        user_role = await self.repo.get_user_role_by_id(user_role_id)
        if not user_role:
            raise NotFoundError(f"User role with ID {user_role_id} not found")
        return to_user_role_response(user_role)

    async def get_user_role(self, user_id: int, role_id: int, status: UserRoleStatus = UserRoleStatus.ACTIVE) -> UserRoleResponse:
        await self.user_service.get_user_by_id(user_id)
        await self.get_role_by_id(role_id)
        user_role = await self.repo.get_user_role(user_id, role_id, status)
        if not user_role:
            raise NotFoundError(f"User role with user ID {user_id} and role ID {role_id} not found")
        return to_user_role_response(user_role)

    async def get_effective_user_roles(self, user_id: int) -> list[UserRoleResponse]:
        await self.user_service.get_user_by_id(user_id)
        effective_user_roles = await self.repo.get_effective_user_roles(user_id)
        return [UserRoleResponse.model_validate(user_role) for user_role in effective_user_roles]

    async def assign_roles_to_user(self, roles_to_user: AssignRolesToUser) -> AssignRolesToUserResponse:
        await self.user_service.get_user_by_id(roles_to_user.user_id)
        try:
            assigned_user_roles = await self.repo.assign_roles_to_user(roles_to_user)
        except IntegrityError as e:
            logging.error(f"Error assigning roles to user: {e}")
            raise BadRequestError(f"Invalid roles to user payload or conflicting roles to user data")
        return assigned_user_roles

    async def revoke_roles_from_user(self, roles_from_user: RevokeRolesFromUser) -> RevokeRolesFromUserResponse:
        await self.user_service.get_user_by_id(roles_from_user.user_id)
        try:
            revoked_user_roles = await self.repo.revoke_roles_from_user(roles_from_user)
        except IntegrityError as e:
            logging.error(f"Error revoking roles from user: {e}")
            raise BadRequestError(f"Invalid roles from user payload or conflicting roles from user data")
        return revoked_user_roles

    async def update_user_role(self, user_role_id: int, user_role_updates: UserRoleUpdate | UserRoleDelete) -> UserRoleResponse:
        user_role = await self.repo.get_user_role_by_id(user_role_id)
        if not user_role:
            raise NotFoundError(f"User role with ID {user_role_id} not found")

        if user_role.status == UserRoleStatus.REVOKED:
            raise BadRequestError(f"Revoked user roles cannot be updated")

        try:
            updated_user_role = await self.repo.update_user_role(user_role, user_role_updates)
        except IntegrityError as e:
            logging.error(f"Error updating user role: {e}")
            raise BadRequestError(f"Invalid user role payload or conflicting user role data")
        return to_user_role_response(updated_user_role)

    """User Permissions"""
    async def has_permission(self, user_id: int, permission_code: str) -> bool:
        await self.user_service.get_user_by_id(user_id)
        
        if await self.repo.user_has_role_code(user_id, "SUPERADMIN"):
            return True

        permission_code = permission_code.strip().upper()
        rules = await self.repo.get_effective_permission_rules_for_user(user_id, permission_code)
        if not rules:
            return False
        return rules[0].effect == RolePermissionEffect.ALLOW