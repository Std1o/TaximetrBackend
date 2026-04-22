from typing import List

from fastapi import APIRouter, Depends

from taximetr import tables
from taximetr.model.schemas import DriverResponse, StopPointCreate, StopPoint
from taximetr.service.driver_service import DriverService
from taximetr.service.order_service import OrderService
from taximetr.service.stop_points import StopPointsService
from taximetr.service.websocket_manager import manager

router = APIRouter(prefix="/stop_points", tags=["stop_points"])


@router.post("/")
async def create_stop_point(
        stop_point: StopPointCreate,
        service: StopPointsService = Depends(),
        order_service: OrderService = Depends(),
        driver_service: DriverService = Depends()
):
    order = order_service.get_order(stop_point.order_id)
    driver = driver_service.get_driver(order.driver_id)
    service.create(stop_point)
    await manager.send_to_order(stop_point.order_id, {
        "type": "status_changed",
        "status": order.status,
        "order": order.model_dump(mode='json'),
        "driver_phone": driver.phone if driver else None,
        "driver_name": driver.name if driver else None,
        "stop_points": service.get_stop_points(stop_point.order_id)
    })


@router.get("/", response_model=List[StopPoint])
def get_stop_points(order_id: int, service: StopPointsService = Depends()):
    return service.get_stop_points(order_id)


@router.delete("/{stop_point_id}")
def delete_stop_point(stop_point_id: int, service: StopPointsService = Depends()):
    service.delete_stop_point(stop_point_id)
