from typing import List

from fastapi import APIRouter, Depends, HTTPException
import asyncio

from taximetr.model.schemas import AlgorithmUpdate, AlgorithmResponse, FactorResponse, DriverResponse, CarResponse, \
    PaymentResponse, SettingsCreate, PercentResponse, Price1HourResponse, Price2HoursResponse, Price8HoursResponse, \
    Price24HoursResponse, Price1MonthResponse
from taximetr.service.auth import get_current_user
from taximetr.service.car_service import CarService
from taximetr.service.driver_service import DriverService
from taximetr.service.settings_service import SettingsService
from taximetr.service.websocket_manager import manager
from taximetr.tables import User

router = APIRouter(prefix="/settings", tags=["settings"])

@router.post("/")
def add_settings(settings_create: SettingsCreate, service: SettingsService = Depends()):
    settings = service.add_settings(settings_create)
    return settings

@router.get("/")
def get_settings(settings_id: int, service: SettingsService = Depends()):
    settings = service.get_settings(settings_id)
    return settings

@router.get("/all")
def get_all_settings(service: SettingsService = Depends()):
    settings = service.get_all_settings()
    return settings


@router.put("/algorithm", response_model=AlgorithmResponse)
async def update_algorithm(
        settings_id: int,
        algorithm_update: AlgorithmUpdate,
        service: SettingsService = Depends()
):
    service.update_algorithm(settings_id, algorithm_update.algorithm)
    return AlgorithmResponse(algorithm=algorithm_update.algorithm)

@router.put("/factor", response_model=FactorResponse)
async def update_factor(
        settings_id: int,
        factor: float,
        service: SettingsService = Depends()
):
    service.update_factor(settings_id, factor)
    return FactorResponse(factor=factor)

@router.put("/payment", response_model=PaymentResponse)
async def update_payment(
        settings_id: int,
        payment: int,
        service: SettingsService = Depends()
):
    service.update_payment(settings_id, payment)
    return PaymentResponse(payment=payment)

@router.put("/percent", response_model=PercentResponse)
async def update_percent(
        settings_id: int,
        percent: int,
        service: SettingsService = Depends()
):
    service.update_percent(settings_id, percent)
    return PercentResponse(percent=percent)

@router.get("/pending", response_model=List[DriverResponse])
def get_pending_drivers(
    settings_id: int,
    service: DriverService = Depends()
):
    return service.get_pending_drivers(settings_id)

@router.put("/{driver_id}/approve")
def approve_driver(
    driver_id: int,
    approved: bool,
    service: DriverService = Depends()
):
    service.approve_driver(driver_id, approved)
    return {"message": f"Driver approved: {approved}", "driver_id": driver_id}

@router.get("/pending/cars", response_model=List[CarResponse])
def get_pending_cars(
    settings_id: int,
    service: CarService = Depends(),
):
    """Руководитель получает список машин, ожидающих одобрения"""
    return service.get_pending_cars(settings_id)


@router.put("/car/{car_id}/approve")
def approve_car(
    car_id: int,
    approved: bool,
    service: CarService = Depends(),
):
    """Руководитель одобряет машину"""
    service.approve_car(car_id, approved)
    return {"message": f"Car approved: {approved}", "car_id": car_id}

@router.put("/price_1_hour", response_model=Price1HourResponse)
async def update_price_1_hour(
        settings_id: int,
        price: int,
        service: SettingsService = Depends()
):
    service.update_price_1_hour(settings_id, price)
    return Price1HourResponse(price_1_hour=price)

@router.put("/price_2_hours", response_model=Price2HoursResponse)
async def update_price_2_hours(
        settings_id: int,
        price: int,
        service: SettingsService = Depends()
):
    service.update_price_2_hours(settings_id, price)
    return Price2HoursResponse(price_2_hours=price)

@router.put("/price_8_hours", response_model=Price8HoursResponse)
async def update_price_8_hours(
        settings_id: int,
        price: int,
        service: SettingsService = Depends()
):
    service.update_price_8_hours(settings_id, price)
    return Price8HoursResponse(price_8_hours=price)

@router.put("/price_24_hours", response_model=Price24HoursResponse)
async def update_price_24_hours(
        settings_id: int,
        price: int,
        service: SettingsService = Depends()
):
    service.update_price_24_hours(settings_id, price)
    return Price24HoursResponse(price_24_hours=price)

@router.put("/price_1_month", response_model=Price1MonthResponse)
async def update_price_1_month(
        settings_id: int,
        price: int,
        service: SettingsService = Depends()
):
    service.update_price_1_month(settings_id, price)
    return Price1MonthResponse(price_1_month=price)