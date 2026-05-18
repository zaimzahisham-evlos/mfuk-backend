"""
SEED SUPER ADMIN DATA
"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.rbac.schema import AssignRolesToUser, AssignUserRole, RoleCreate, RoleStatus
from app.user.models import UserType
from app.user.schema import UserCreate, UserStatus
from app.core.exceptions import NotFoundError
from app.rbac.services import RbacService
from sqlalchemy.ext.asyncio import AsyncSession

from app.user.services import UserService
from app.db.session import get_db, AsyncSessionLocal
from app.core.config import settings

async def seed_super_admin(db: AsyncSession | None = None):
    
    async def _seed(db: AsyncSession):
        rbac_service = RbacService(db)
        user_service = UserService(db)
        
        try:
            role = await rbac_service.get_role_by_code("SUPERADMIN")
        except NotFoundError:
            role = await rbac_service.create_role(
                RoleCreate(
                    role_code="SUPERADMIN",
                    role_name="Super Admin",
                    auth_required=False,
                    is_system_role=True,
                    status=RoleStatus.ACTIVE,
                )
            )

        try:
            user = await user_service.get_user_by_user_code("SUPERADMIN")
        except NotFoundError:
            user = await user_service.create_user(
                UserCreate(
                    user_code="SUPERADMIN",
                    full_name="Super Admin",
                    user_type=UserType.HUMAN,
                    status=UserStatus.ACTIVE,
                    password=settings.SUPERADMIN_PASSWORD,
                )
            )

        await rbac_service.assign_roles_to_user(
            AssignRolesToUser(
                user_id=user.id,
                user_roles=[AssignUserRole(role_id=role.id)],
            )
        )

    if db:
        await _seed(db)
    else:
        async with AsyncSessionLocal() as session:
            await _seed(session)

if __name__ == "__main__":
    asyncio.run(seed_super_admin())
