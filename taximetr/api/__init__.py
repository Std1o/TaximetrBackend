from fastapi import APIRouter
from .auth import router as auth_router
from .drivers import router as drivers_router
from .orders import router as orders_router
from .settings import router as settings_router
from .websocket import router as websocket_router
from .tariffs import router as tariffs_router
from .cars import router as cars_router
from .notifications import router as notifications_router
from .images import router as images_router
from .drivers_tickets import router as drivers_tickets_router
from .tickets import router as tickets_router
from .premium import router as premium_router
from .stop_points import router as stop_points_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(drivers_router)
router.include_router(orders_router)
router.include_router(settings_router)
router.include_router(websocket_router)
router.include_router(tariffs_router)
router.include_router(cars_router)
router.include_router(notifications_router)
router.include_router(images_router)
router.include_router(drivers_tickets_router)
router.include_router(tickets_router)
router.include_router(premium_router)
router.include_router(stop_points_router)