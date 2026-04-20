from fastapi import APIRouter, Depends, HTTPException
from typing import List

from taximetr.model.schemas import DriverResponse, DriverCreate, DriverUpdateLocation
from taximetr.service.auth import get_current_user
from taximetr.service.driver_service import DriverService
from taximetr.service.order_service import OrderService
from taximetr.service.websocket_manager import manager
from taximetr.tables import User

router = APIRouter(prefix="/drivers", tags=["drivers"])

@router.post("/", response_model=DriverResponse)
def create_driver(
    driver: DriverCreate,
    service: DriverService = Depends(),
    current_user: User = Depends(get_current_user)
):
    driver_data = driver.model_dump()
    driver_data["user_id"] = current_user.id
    return service.create_driver(DriverCreate(**driver_data))

@router.get("/", response_model=List[DriverResponse])
def get_drivers(service: DriverService = Depends()):
    return service.get_all_drivers()

@router.get("/{user_id}", response_model=DriverResponse)
def get_driver(user_id: int, service: DriverService = Depends()):
    driver = service.get_driver_by_user_id(user_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver

@router.put("/{driver_id}/location")
async def update_location(
        driver_id: int,
        location: DriverUpdateLocation,
        driver_service: DriverService = Depends(),
        order_service: OrderService = Depends()
):
    driver = driver_service.update_location(driver_id, location)
    order = order_service.get_order(driver.current_order_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    # Если у водителя есть активный заказ, отправляем координаты клиенту
    if driver.current_order_id:
        await manager.send_to_role_in_order(
            driver.current_order_id,
            "client",
            {
                "type": "driver_location",
                "lat": location.lat,
                "lng": location.lng,
                "driver_id": driver_id,
                "driver_name": driver.name,
                "order_id": order.id,
                "status": order.status,
                "order": order.model_dump(mode='json'),
                "driver_phone": driver.phone,
            }
        )

    return {"message": "Location updated", "driver_id": driver_id}

@router.put("/{driver_id}/online")
def set_online(driver_id: int, service: DriverService = Depends()):
    driver = service.set_online(driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return {"message": "Driver is online", "driver_id": driver_id}

@router.put("/{driver_id}/offline")
def set_offline(driver_id: int, service: DriverService = Depends()):
    driver = service.set_offline(driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return {"message": "Driver is offline", "driver_id": driver_id}

@router.delete("/{driver_id}")
def delete_driver(driver_id: int, service: DriverService = Depends()):
    service.delete_driver(driver_id)