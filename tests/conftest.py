import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from alembic import command
from alembic.config import Config

from app.main import app
from app.db.session import get_db
from app.core.config import settings
from app.rbac.models import PermissionCategory
from app.user.models import UserStatus, UserType

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    alembic_config = Config("alembic.ini")
    alembic_config.set_main_option("sqlalchemy.url", settings.TEST_DATABASE_URL)
    alembic_config.set_main_option("script_location", "app/db/migrations")
    command.upgrade(alembic_config, "head")
    yield

@pytest.fixture(scope="function")
async def db_session(setup_database):
    engine = create_async_engine(settings.TEST_DATABASE_URL)
    async with engine.connect() as conn:
        transaction = await conn.begin()
        
        async_session = async_sessionmaker(conn, class_=AsyncSession, expire_on_commit=False, autoflush=False, autocommit=False)
        async with async_session() as session:
            from app.db.seed.superadmin import seed_super_admin
            from app.db.seed.permissions import seed_initial_permissions

            await seed_super_admin(session)
            await seed_initial_permissions(session)

            yield session

        await transaction.rollback()
        
    await engine.dispose()

@pytest.fixture(scope="function")
async def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
async def authorized_client_human_no_role(client, db_session):
    """Creates a user with no roles, generates a token, and inject to client headers"""
    from app.user.services import UserService
    from app.user.schema import UserCreate
    from app.auth.services import AuthenticationService

    user_service = UserService(db_session)
    user_data = UserCreate(
        user_code="testuser",
        full_name="Test User",
        user_type=UserType.HUMAN,
        status=UserStatus.ACTIVE,
        password="password"
    )
    await user_service.create_user(user_data)

    token = await AuthenticationService(db_session).login_user_by_user_code(user_data.user_code, user_data.password)

    client.headers["Authorization"] = f"Bearer {token.access_token}"
    yield client

@pytest.fixture(scope="function")
async def authorized_client_non_human(client, db_session):
    """Creates a non human user with no roles, generates a token, and inject to client headers"""
    from app.user.services import UserService
    from app.user.schema import UserCreate
    from app.auth.services import AuthenticationService

    user_service = UserService(db_session)
    user_data = UserCreate(
        user_code="testusernonhuman",
        full_name="Test User Non Human",
        user_type=UserType.SYSTEM,
        status=UserStatus.ACTIVE,
        password=None
    )
    await user_service.create_user(user_data)

    token = await AuthenticationService(db_session).login_user_by_user_code(user_data.user_code, user_data.password)

    client.headers["Authorization"] = f"Bearer {token.access_token}"
    yield client

@pytest.fixture(scope="function")
async def authorized_client_superadmin(client, db_session):
    """gets seeded superadmin user and generates a token, and inject to client headers"""
    from app.user.services import UserService
    from app.auth.services import AuthenticationService

    user = await UserService(db_session).get_user_by_user_code("SUPERADMIN")

    token = await AuthenticationService(db_session).login_user_by_user_code(user.user_code, settings.SUPERADMIN_PASSWORD)

    client.headers["Authorization"] = f"Bearer {token.access_token}"
    yield client

@pytest.fixture(scope="function")
async def authorized_client_user_manager(client, db_session):
    """Creates a user with a role that has permissions to update users, generates a token, and inject to client headers"""
    from app.user.services import UserService
    from app.user.schema import UserCreate
    from app.auth.services import AuthenticationService
    from app.rbac.services import RbacService
    from app.rbac.schema import RoleCreate
    from app.rbac.schema import AssignPermissionsToRole, AssignRolePermission, AssignRolesToUser, AssignUserRole

    rbac_service = RbacService(db_session)
    role_data = RoleCreate(
        role_code="USER_MANAGER",
        role_name="User Manager",
    )
    role = await rbac_service.create_role(role_data)

    permission_service = RbacService(db_session)
    permissions = await permission_service.get_permissions(modules=["USER"])
    permissions_to_role = AssignPermissionsToRole(
        role_id=role.id,
        role_permissions=[
            AssignRolePermission(
                permission_id=permission.id,
            )
            for permission in permissions
        ]
    )

    await rbac_service.assign_permissions_to_role(permissions_to_role)

    user_service = UserService(db_session)
    user_data = UserCreate(
        user_code="usermanager",
        full_name="User Manager",
        password="password",
    )
    user = await user_service.create_user(user_data)
    await rbac_service.assign_roles_to_user(
        AssignRolesToUser(
            user_id=user.id, 
            user_roles=[AssignUserRole(role_id=role.id)]
        )
    )

    token = await AuthenticationService(db_session).login_user_by_user_code(user_data.user_code, user_data.password)

    client.headers["Authorization"] = f"Bearer {token.access_token}"
    yield client

@pytest.fixture(scope="function")
async def authorized_client_rbac_manager(client, db_session):
    """Creates a user with a role that has permissions to update roles and permissions, generates a token, and inject to client headers"""
    from app.rbac.services import RbacService
    from app.rbac.schema import RoleCreate
    from app.rbac.schema import AssignPermissionsToRole, AssignRolePermission, AssignRolesToUser, AssignUserRole
    from app.user.services import UserService
    from app.user.schema import UserCreate
    from app.auth.services import AuthenticationService
    from app.rbac.models import RolePermissionStatus

    rbac_service = RbacService(db_session)
    role_data = RoleCreate(
        role_code="RBAC_MANAGER",
        role_name="RBAC Manager",
    )
    role = await rbac_service.create_role(role_data)

    permission_service = RbacService(db_session)
    permissions = await permission_service.get_permissions(modules=["user", "role", "role_permission", "permission", "user_role"])
    permissions_to_role = AssignPermissionsToRole(
        role_id=role.id,
        role_permissions=[
            AssignRolePermission(
                permission_id=permission.id,
                status=RolePermissionStatus.INACTIVE if permission.category in [PermissionCategory.OVERRIDE] else RolePermissionStatus.ACTIVE,
            )
            for permission in permissions
        ]
    )
    await rbac_service.assign_permissions_to_role(permissions_to_role)

    user_service = UserService(db_session)
    user_data = UserCreate(
        user_code="rbacmanager",
        full_name="RBAC Manager",
        password="password",
    )
    user = await user_service.create_user(user_data)
    await rbac_service.assign_roles_to_user(
        AssignRolesToUser(
            user_id=user.id, 
            user_roles=[AssignUserRole(role_id=role.id)]
        )
    )

    token = await AuthenticationService(db_session).login_user_by_user_code(user_data.user_code, user_data.password)
    client.headers["Authorization"] = f"Bearer {token.access_token}"
    yield client