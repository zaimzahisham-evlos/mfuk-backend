"""
SEED INITIAL PERMISSIONS DATA 
"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.core.exceptions import NotFoundError
from app.rbac.models import PermissionCategory
from app.rbac.schema import PermissionCreate, PermissionStatus
from app.rbac.services import RbacService
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db, AsyncSessionLocal

async def seed_initial_permissions(db: AsyncSession | None = None, modules: list[str] | None = None):
    async def _seed(db: AsyncSession, modules: list[str] | None = None):
        rbac_service = RbacService(db)
        if modules is None:
            modules = [
                "user", "permission", "role", "role_permission", "user_role",
                "machine", "sku", "recipe", "recipe_version", "repository_image",
            ]
        for module in modules:
            for permission in PermissionCategory:
                module_name = module.split("_")
                if len(module_name) > 1:
                    module_name = f"{module_name[0].capitalize()} {module_name[1].capitalize()}"
                else:
                    module_name = module_name[0].capitalize()

                permission_code = f"{module.upper()}_{permission.upper()}"
                permission_name = f"{module.capitalize()} {permission.capitalize()}"

                try:
                    await rbac_service.get_permission_by_code(permission_code)
                except NotFoundError:
                    await rbac_service.create_permission(
                        PermissionCreate(
                            permission_code=permission_code,
                            permission_name=permission_name,
                            module=module.title(),
                            category=permission,
                        )
                    )
        
        
    if db:
        await _seed(db, modules)
    else:
        async with AsyncSessionLocal() as session:
            await _seed(session, modules)

if __name__ == "__main__":
    asyncio.run(seed_initial_permissions())