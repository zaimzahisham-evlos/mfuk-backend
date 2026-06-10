import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from alembic import command
from alembic.config import Config

from app.main import app
from app.db.session import get_db
from app.core.config import settings
from app.user.models import UserType
from tests.utils import create_user

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
    from app.auth.services import AuthenticationService

    user = await create_user(db_session, full_name="test user")
    token = await AuthenticationService(db_session).login_user_by_user_code(user.user_code, "password")

    client.headers["Authorization"] = f"Bearer {token.access_token}"
    yield client

@pytest.fixture(scope="function")
async def authorized_client_non_human(client, db_session):
    """Creates a non human user with no roles, generates a token, and inject to client headers"""
    from app.auth.services import AuthenticationService

    user = await create_user( 
        db_session, 
        full_name="Test User Non Human",
        user_type=UserType.SYSTEM,
    )

    token = await AuthenticationService(db_session).login_user_by_user_code(user.user_code, None)

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
    from app.auth.services import AuthenticationService

    user = await create_user(
        db_session, 
        full_name="user manager",
        role_code="USER_MANAGER",
        permission_modules=["USER"],
    )

    token = await AuthenticationService(db_session).login_user_by_user_code(user.user_code, "password")

    client.headers["Authorization"] = f"Bearer {token.access_token}"
    yield client

@pytest.fixture(scope="function")
async def authorized_client_rbac_manager(client, db_session):
    """Creates a user with a role that has permissions to update roles and permissions, generates a token, and inject to client headers"""
    from app.auth.services import AuthenticationService

    user = await create_user(
        db_session,
        full_name="rbac manager",
        role_code="RBAC_MANAGER",
        permission_modules=["user", "role", "role_permission", "permission", "user_role"],
    )

    token = await AuthenticationService(db_session).login_user_by_user_code(user.user_code, "password")
    client.headers["Authorization"] = f"Bearer {token.access_token}"
    yield client

@pytest.fixture(scope="function")
async def authorized_client_admin(client, db_session):
    """Creates an Admin user that has all permissions to all modules"""
    from app.auth.services import AuthenticationService

    user = await create_user(
        db_session, 
        full_name="admin",
        role_code="ADMIN",
    )

    token = await AuthenticationService(db_session).login_user_by_user_code(user.user_code, "password")
    client.headers["Authorization"] = f"Bearer {token.access_token}"
    yield client

@pytest.fixture(scope="function")
async def seeded_machines(db_session):
    from app.production.services import ProductionService
    from app.production.schema import MachineCreate
    from app.production.models import MachineStatus

    production_service = ProductionService(db_session)
    machines = [
        MachineCreate(
            machine_code="MFUK_M00",
            machine_name="Machine 00",
            status=MachineStatus.ACTIVE,
        ),
        MachineCreate(
            machine_code="MFUK_M99",
            machine_name="Machine 99",
            status=MachineStatus.MAINTENANCE,
        ),
    ]
    created_machines = []
    for machine_data in machines:
        machine = await production_service.create_machine(machine_data)
        created_machines.append(machine)
    
    yield created_machines

@pytest.fixture(scope="function")
async def seeded_skus(db_session):
    from app.production.services import ProductionService
    from app.production.schema import SKUCreate
    from app.production.models import SKUStatus

    production_service = ProductionService(db_session)
    skus = [
        SKUCreate(
            sku_code="TEST_SKU_00",
            sku_name="Test SKU 00",
            status=SKUStatus.ACTIVE,
        ),
        SKUCreate(
            sku_code="TEST_SKU_99",
            sku_name="Test SKU 99",
            status=SKUStatus.INACTIVE,
        ),
    ]
    created_skus = []
    for sku_data in skus:
        sku = await production_service.create_sku(sku_data)
        created_skus.append(sku)

    yield created_skus

@pytest.fixture(scope="function")
async def seeded_recipes(db_session, seeded_skus, seeded_machines):
    from app.production.services import ProductionService
    from app.production.schema import RecipeCreate
    from app.production.models import RecipeStatus

    production_service = ProductionService(db_session)
    recipes = [
        RecipeCreate(
            recipe_code="TEST_RECIPE_00",
            recipe_name="Test Recipe 00",
            sku_id=seeded_skus[0].id,
            machine_id=seeded_machines[0].id,
            status=RecipeStatus.ACTIVE,
        ),
        RecipeCreate(
            recipe_code="TEST_RECIPE_01",
            recipe_name="Test Recipe 01",
            sku_id=seeded_skus[0].id,
            machine_id=seeded_machines[1].id,
            status=RecipeStatus.ACTIVE,
        ),
        RecipeCreate(
            recipe_code="TEST_RECIPE_10",
            recipe_name="Test Recipe 02",
            sku_id=seeded_skus[1].id,
            machine_id=seeded_machines[0].id,
            status=RecipeStatus.INACTIVE,
        )
    ]
    created_recipes = []
    for recipe_data in recipes:
        recipe = await production_service.create_recipe(recipe_data)
        created_recipes.append(recipe)

    yield created_recipes

@pytest.fixture(scope="function")
async def seeded_recipe_versions(db_session, seeded_recipes):
    from app.production.services import ProductionService
    from app.production.schema import RecipeVersionCreate

    production_service = ProductionService(db_session)
    recipe_versions = [
        RecipeVersionCreate(
            recipe_id=seeded_recipes[0].id,
            version_code="TEST_RECIPE_VERSION_001",
            version_name="Test Recipe Version 001",
        ),
        RecipeVersionCreate(
            recipe_id=seeded_recipes[0].id,
            version_code="TEST_RECIPE_VERSION_002",
            version_name="Test Recipe Version 002",
            approval_required=False,
        ),
        RecipeVersionCreate(
            recipe_id=seeded_recipes[1].id,
            version_code="TEST_RECIPE_VERSION_011",
            version_name="Test Recipe Version 011",
            approval_required=False,
        ),
    ]
    created_recipe_versions = []
    for recipe_version_data in recipe_versions:
        recipe_version = await production_service.create_recipe_version(recipe_version_data)
        created_recipe_versions.append(recipe_version)