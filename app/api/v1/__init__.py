from fastapi import APIRouter

from app.api.v1.auth_router import router as auth_router
from app.api.v1.health_router import router as health_router

router = APIRouter(prefix="/api/v1")

router.include_router(auth_router)
router.include_router(health_router)