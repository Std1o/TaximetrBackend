from fastapi import APIRouter, Depends, HTTPException
from typing import List

from taximetr.model.schemas import DriverResponse, DriverCreate, DriverUpdateLocation
from taximetr.service.auth import get_current_user, AuthService
from taximetr.service.car_service import CarService
from taximetr.service.driver_service import DriverService
from taximetr.service.order_service import OrderService
from taximetr.service.stop_points import StopPointsService
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
def get_drivers(settings_id: int, service: DriverService = Depends()):
    return service.get_all_drivers(settings_id)


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
        order_service: OrderService = Depends(),
        stop_points_service: StopPointsService = Depends(),
        car_service: CarService = Depends()
):
    driver = driver_service.update_location(driver_id, location)
    car = car_service.get_car(driver.current_car_id) if driver else None
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
                "license_plate": car.license_plate if car else None,
                "stop_points": [sp.model_dump(mode='json') for sp in stop_points_service.get_stop_points(order.id)]
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
def delete_driver(driver_id: int, service: DriverService = Depends(), auth_service: AuthService = Depends()):
    driver = service.get_driver(driver_id)
    service.delete_driver(driver_id)
    auth_service.delete_user(driver.user_id)

@router.put("/{driver_id}/set_current_car", response_model=DriverResponse)
def set_current_car(driver_id: int, car_id: int, service: DriverService = Depends()):
    driver = service.set_current_car(driver_id, car_id)
    return driver
