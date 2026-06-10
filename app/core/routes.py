from fastapi import APIRouter
from ..user.routes import router as user_router
from ..auth.routes import router as auth_router
from ..rbac.routes import router as rbac_router
from ..production.routes import router as production_router
from app.storage.dependencies import get_storage_client

router = APIRouter()

router.include_router(router=user_router, prefix="/users", tags=["users"])
router.include_router(router=auth_router, prefix="/auth", tags=["auth"])
router.include_router(router=rbac_router, prefix="/authorization", tags=["authorization"])
router.include_router(router=production_router, prefix="/production", tags=["production"])

@router.get("/health")
async def health():
    # add DB check later
    storage_ok = get_storage_client().ping()
    return {
        "status": "ok" if storage_ok else "degraded",
        "storage_ok": "ok" if storage_ok else "unavailable",
    }
