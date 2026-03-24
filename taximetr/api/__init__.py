from fastapi import APIRouter
from .auth import router as auth_router
from .drivers import router as drivers_router
from .orders import router as orders_router
from .settings import router as settings_router
from .websocket import router as websocket_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(drivers_router)
router.include_router(orders_router)
router.include_router(settings_router)
router.include_router(websocket_router)