from fastapi import APIRouter, Response, status, Depends, Query
from app.auth.dependencies import require_permission
from app.core.pagination import PaginatedResponse, PaginationParams
from app.core.utils import utcnow
from app.user.schema import UserResponse
from ..rbac.schema import *
from ..rbac.services import RbacService
import logging
from typing import Annotated, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.session import get_db

router = APIRouter()

"""Permissions"""
@router.get("/permissions", response_model=PaginatedResponse[PermissionResponse])
async def get_permissions(
    current_user: Annotated[UserResponse, Depends(require_permission("PERMISSION_VIEW"))], 
    db: Annotated[AsyncSession, Depends(get_db)],
    pagination: Annotated[PaginationParams, Depends()],
    include_deleted: bool = False,
    modules: Annotated[list[str] | None, Query()] = None,
    statuses: Annotated[list[PermissionStatus] | None, Query()] = None,
):
    logging.info(f"Getting permissions for modules {modules if modules else 'all'}")
    return await RbacService(db).get_permissions(include_deleted, modules, statuses, pagination)

@router.get("/permissions/{permission_code}", response_model=PermissionResponse)
async def get_permission_by_code(
    permission_code: str,
    current_user: Annotated[UserResponse, Depends(require_permission("PERMISSION_VIEW"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    logging.info(f"Getting permission by code {permission_code}")
    return await RbacService(db).get_permission_by_code(permission_code)

@router.post("/permissions", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED)
async def create_permission(
    permission: PermissionCreateRequest,
    current_user: Annotated[UserResponse, Depends(require_permission("PERMISSION_CREATE"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    logging.info(f"Creating permission {permission.permission_code}")
    permission_create = PermissionCreate(
        **permission.model_dump(exclude_unset=True),
        created_by_id=current_user.id
    )
    return await RbacService(db).create_permission(permission_create)

@router.patch("/permissions/{permission_code}", response_model=PermissionResponse)
async def update_permission(
    permission_code: str,
    permission: PermissionUpdateRequest,
    current_user: Annotated[UserResponse, Depends(require_permission("PERMISSION_UPDATE"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    logging.info(f"Updating permission {permission_code}")
    permission_updates = PermissionUpdate(
        **permission.model_dump(exclude_unset=True),
        updated_by_id=current_user.id
    )

    return await RbacService(db).update_permission(permission_code, permission_updates)

@router.delete("/permissions/{permission_code}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_permission(
    permission_code: str,
    current_user: Annotated[UserResponse, Depends(require_permission("PERMISSION_DELETE"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    logging.info(f"Deleting permission {permission_code}")
    return await RbacService(db).delete_permission(permission_code, current_user.id)

"""Roles"""
@router.get("/roles", response_model=PaginatedResponse[RoleResponse])
async def get_roles(
    current_user: Annotated[UserResponse, Depends(require_permission("ROLE_VIEW"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    pagination: Annotated[PaginationParams, Depends()],
    include_deleted: bool = False,
    statuses: Annotated[list[RoleStatus] | None, Query()] = None,
):
    logging.info(f"Getting roles")
    return await RbacService(db).get_roles(include_deleted, statuses, pagination)

@router.get("/roles/{role_code}", response_model=RoleResponse)
async def get_role_by_code(
    role_code: str,
    current_user: Annotated[UserResponse, Depends(require_permission("ROLE_VIEW"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    logging.info(f"Getting role by code {role_code}")
    return await RbacService(db).get_role_by_code(role_code)

@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role: RoleCreateRequest,
    current_user: Annotated[UserResponse, Depends(require_permission("ROLE_CREATE"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    logging.info(f"Creating role {role.role_code}")
    role_create = RoleCreate(
        **role.model_dump(exclude_unset=True),
        created_by_id=current_user.id
    )
    return await RbacService(db).create_role(role_create)

@router.patch("/roles/{role_code}", response_model=RoleResponse)
async def update_role(
    role_code: str,
    role: RoleUpdateRequest,
    current_user: Annotated[UserResponse, Depends(require_permission("ROLE_UPDATE"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    logging.info(f"Updating role {role_code}")
    role_updates = RoleUpdate(
        **role.model_dump(exclude_unset=True),
        updated_by_id=current_user.id
    )
    return await RbacService(db).update_role(role_code, role_updates)

@router.delete("/roles/{role_code}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_code: str,
    current_user: Annotated[UserResponse, Depends(require_permission("ROLE_DELETE"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    logging.info(f"Deleting role {role_code}")
    return await RbacService(db).delete_role(role_code, current_user.id)

"""Role Permissions"""
@router.get("/roles/{role_id}/permissions", response_model=list[RolePermissionResponse])
async def get_role_permissions(
    role_id: int,
    current_user: Annotated[UserResponse, Depends(require_permission("ROLE_PERMISSION_VIEW"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    include_deleted: bool = False,
    statuses: Annotated[Sequence[RolePermissionStatus] | None, Query()] = None,
):
    logging.info(f"Getting role permissions for role {role_id} with statuses {statuses if statuses else 'all'}")
    return await RbacService(db).get_role_permissions(role_id, include_deleted, statuses)

@router.get("/role-permission/{role_permission_id}", response_model=RolePermissionResponse)
async def get_role_permission(
    role_permission_id: int,
    current_user: Annotated[UserResponse, Depends(require_permission("ROLE_PERMISSION_VIEW"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    logging.info(f"Getting role permission {role_permission_id}")
    return await RbacService(db).get_role_permission_by_id(role_permission_id)

@router.post("/roles/{role_id}/permissions", response_model=AssignPermissionsToRoleResponse)
async def assign_permissions_to_role(
    role_id: int,
    role_permissions: AssignPermissionsToRoleRequest,
    current_user: Annotated[UserResponse, Depends(require_permission("ROLE_PERMISSION_ASSIGN"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    logging.info(f"Assigning permissions to role {role_id}")
    permissions_to_role = AssignPermissionsToRole(
        **role_permissions.model_dump(exclude_unset=True),
        role_id=role_id,
        created_by_id=current_user.id
    )
    return await RbacService(db).assign_permissions_to_role(permissions_to_role)

@router.patch("/roles/{role_id}/permissions/revoke", response_model=RevokePermissionsFromRoleResponse)
async def revoke_permissions_from_role(
    role_id: int,
    role_permissions: RevokePermissionsFromRoleRequest,
    current_user: Annotated[UserResponse, Depends(require_permission("ROLE_PERMISSION_REVOKE"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):

    logging.info(f"Revoking permissions from role {role_id} for permissions {role_permissions}")
    role_permissions = RevokePermissionsFromRole(
            role_id=role_id,
            role_permissions=role_permissions.role_permissions,
            updated_by_id=current_user.id,
            deleted_by_id=current_user.id,
        )
    return await RbacService(db).revoke_permissions_from_role(role_permissions)

@router.patch("/role-permission/{role_permission_id}", response_model=RolePermissionResponse)
async def update_role_permission(
    role_permission_id: int,
    role_permission: RolePermissionUpdateRequest,
    current_user: Annotated[UserResponse, Depends(require_permission("ROLE_PERMISSION_UPDATE"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    logging.info(f"Updating role permission for role permission {role_permission_id}")
    role_permission_updates = RolePermissionUpdate(
        **role_permission.model_dump(exclude_unset=True),
        updated_by_id=current_user.id
    )
    return await RbacService(db).update_role_permission(role_permission_id, role_permission_updates)

@router.delete("/role-permission/{role_permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role_permission(
    role_permission_id: int,
    current_user: Annotated[UserResponse, Depends(require_permission("ROLE_PERMISSION_DELETE"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    logging.info(f"Deleting role permission for role permission {role_permission_id}")
    role_permission_updates = RolePermissionUpdate(
        status=RolePermissionStatus.DELETED,
        updated_by_id=current_user.id,
        deleted_by_id=current_user.id,
        deleted_at=utcnow(),
    )
    await RbacService(db).update_role_permission(role_permission_id, role_permission_updates)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


"""User Roles"""
@router.get("/users/{user_id}/roles", response_model=list[UserRoleResponse])
async def get_user_roles(
    user_id: int,
    current_user: Annotated[UserResponse, Depends(require_permission("USER_ROLE_VIEW"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    include_deleted: bool = False,
    statuses: Annotated[Sequence[UserRoleStatus] | None, Query()] = None,
    include_active_effective: bool = True,
):
    logging.info(f"Getting user roles for user {user_id}")
    return await RbacService(db).get_user_roles(user_id, include_deleted, statuses, include_active_effective)

@router.get("/user-role/{user_role_id}", response_model=UserRoleResponse)
async def get_user_role(
    user_role_id: int,
    current_user: Annotated[UserResponse, Depends(require_permission("USER_ROLE_VIEW"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    logging.info(f"Getting user role for id {user_role_id}")
    return await RbacService(db).get_user_role_by_id(user_role_id)

@router.post("/users/{user_id}/roles", response_model=AssignRolesToUserResponse)
async def assign_roles_to_user(
    user_id: int,
    roles_to_user: AssignRolesToUserRequest,
    current_user: Annotated[UserResponse, Depends(require_permission("USER_ROLE_ASSIGN"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    logging.info(f"Assigning roles to user {user_id}")
    roles_to_user = AssignRolesToUser(
        **roles_to_user.model_dump(exclude_unset=True),
        user_id=user_id,
        created_by_id=current_user.id,
        assigned_by_id=current_user.id,
    )
    return await RbacService(db).assign_roles_to_user(roles_to_user)

@router.patch("/users/{user_id}/roles/revoke", response_model=RevokeRolesFromUserResponse)
async def revoke_roles_from_user(
    user_id: int,
    roles_from_user: RevokeRolesFromUserRequest,
    current_user: Annotated[UserResponse, Depends(require_permission("USER_ROLE_REVOKE"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    user_roles = [f"{user_role.user_role_id}" for user_role in roles_from_user.user_roles]
    logging.info(f"Revoking user roles {', '.join(user_roles)} from user {user_id}")
    roles_from_user = RevokeRolesFromUser(
            user_id=user_id,
            user_roles=roles_from_user.user_roles,
            updated_by_id=current_user.id,
            revoked_by_id=current_user.id,
            revoked_at=utcnow(),
        )
    return await RbacService(db).revoke_roles_from_user(roles_from_user)

@router.patch("/user-role/{user_role_id}", response_model=UserRoleResponse)
async def update_user_role(
    user_role_id: int,
    user_role: UserRoleUpdateRequest,
    current_user: Annotated[UserResponse, Depends(require_permission("USER_ROLE_UPDATE"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    logging.info(f"Updating user role for user role {user_role_id}")
    user_role_updates = UserRoleUpdate(
        **user_role.model_dump(exclude_unset=True),
        updated_by_id=current_user.id,
    )
    return await RbacService(db).update_user_role(user_role_id, user_role_updates)

@router.delete("/user-role/{user_role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_role(
    user_role_id: int,
    current_user: Annotated[UserResponse, Depends(require_permission("USER_ROLE_DELETE"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    logging.info(f"Deleting user role for user role {user_role_id}")
    user_role_updates = UserRoleDelete(
        status=UserRoleStatus.DELETED,
        updated_by_id=current_user.id,
        deleted_by_id=current_user.id,
        deleted_at=utcnow(),
    )
    await RbacService(db).update_user_role(user_role_id, user_role_updates)

    return Response(status_code=status.HTTP_204_NO_CONTENT)