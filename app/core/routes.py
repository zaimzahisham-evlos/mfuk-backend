from fastapi import APIRouter
from ..user.routes import router as user_router
from ..auth.routes import router as auth_router
from ..rbac.routes import router as rbac_router

router = APIRouter()

router.include_router(router=user_router, prefix="/users", tags=["users"])
router.include_router(router=auth_router, prefix="/auth", tags=["auth"])
router.include_router(router=rbac_router, prefix="/authorization", tags=["authorization"])
