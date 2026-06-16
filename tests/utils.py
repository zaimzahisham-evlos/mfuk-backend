from app.core.pagination import PaginationParams
from app.user.services import UserService
from app.user.schema import UserCreate
from app.rbac.services import RbacService
from app.rbac.schema import RoleCreate
from app.rbac.models import RolePermissionStatus, PermissionCategory
from app.rbac.schema import AssignPermissionsToRole, AssignRolePermission, AssignRolesToUser, AssignUserRole
from app.user.models import UserType

async def create_user(db_session, full_name: str, user_type: UserType = UserType.HUMAN, role_code: str | None = None, permission_modules: list[str] | None = None):

    user_service = UserService(db_session)
    user_data = UserCreate(
        user_code=full_name.upper().replace(" ", ""),
        full_name=full_name.title(),
        user_type=user_type,
        password="password" if user_type == UserType.HUMAN else None,
    )
    user = await user_service.create_user(user_data)

    if role_code:
        rbac_service = RbacService(db_session)
        role_data = RoleCreate(
            role_code=role_code,
            role_name=role_code.replace("_", " "),
        )
        role = await rbac_service.create_role(role_data)
        
        permissions_page = await rbac_service.get_permissions(modules=permission_modules, pagination=PaginationParams(page=1, limit=100, search=""))
        permissions = permissions_page.items
        permissions_to_role = AssignPermissionsToRole(
            role_id=role.id,
            role_permissions=[
                AssignRolePermission(
                    permission_id=permission.id,
                    status=RolePermissionStatus.INACTIVE 
                        if permission.category in [PermissionCategory.OVERRIDE] 
                        else RolePermissionStatus.ACTIVE,
                ) for permission in permissions]
        )
        await rbac_service.assign_permissions_to_role(permissions_to_role)
        await rbac_service.assign_roles_to_user(AssignRolesToUser(user_id=user.id, user_roles=[AssignUserRole(role_id=role.id)]))
    
    return user