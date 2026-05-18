from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import with_loader_criteria, Session
from ..core.config import settings
from ..db.mixins import SoftDeleteMixin
from sqlalchemy import event

engine = create_async_engine(settings.DATABASE_URL, echo=True)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False, autoflush=False, autocommit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def close_db(db: AsyncSession):
    await db.close()

@event.listens_for(Session, "do_orm_execute")
def _exclude_soft_deleted(execute_state):
    if execute_state.is_select and not execute_state.execution_options.get("include_deleted", False):
        execute_state.statement = execute_state.statement.options(
            with_loader_criteria(
                SoftDeleteMixin,
                lambda cls: cls.deleted_at.is_(None),
                include_aliases=True,
            )
        )

def include_deleted_execution_options(include_deleted: bool) -> dict:
    if include_deleted:
        return {"include_deleted": True}
    return {}