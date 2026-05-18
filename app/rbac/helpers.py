from typing import Sequence
from sqlalchemy import Select, and_, func, or_

from app.rbac.models import UserRole, UserRoleStatus
from app.rbac.schema import RolePermissionResponse, RolePermission, UserRoleResponse

def effective_now_clause(model):
    now = func.now()
    return (
        or_(model.valid_from.is_(None), model.valid_from <= now),
        or_(model.valid_until.is_(None), model.valid_until > now),
    )

def active_effective_user_role_clause(query: Select, statuses: Sequence[UserRoleStatus]) -> Select:
    non_active_statuses = [status for status in statuses if status != UserRoleStatus.ACTIVE]
    active_effective = and_(
        UserRole.status == UserRoleStatus.ACTIVE,
        *effective_now_clause(UserRole)
    )
    if non_active_statuses:
        query = query.where(
            or_(UserRole.status.in_(non_active_statuses), active_effective)
        )
    else:
        query = query.where(active_effective)

    return query

def to_role_permission_response(role_permission: RolePermission) -> RolePermissionResponse:
    dto = RolePermissionResponse.model_validate(role_permission)
    dto.role_code = role_permission.role.role_code if role_permission.role else None
    dto.permission_code = role_permission.permission.permission_code if role_permission.permission else None
    dto.role_status = role_permission.role.status if role_permission.role else None
    dto.permission_status = role_permission.permission.status if role_permission.permission else None
    return dto

def to_user_role_response(user_role: UserRole) -> UserRoleResponse:
    dto = UserRoleResponse.model_validate(user_role)
    dto.user_code = user_role.user.user_code if user_role.user else None
    dto.role_code = user_role.role.role_code if user_role.role else None
    dto.user_status = user_role.user.status if user_role.user else None
    dto.role_status = user_role.role.status if user_role.role else None
    return dto