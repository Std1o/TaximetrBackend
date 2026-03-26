from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from taximetr.model.enums import DriverStatus, OrderStatus, DistributionAlgorithm


class DriverCreate(BaseModel):
    name: str
    phone: str
    settings_id: int


class DriverResponse(BaseModel):
    id: int
    name: str
    phone: str
    status: DriverStatus
    current_lat: float
    current_lng: float
    current_order_id: Optional[int]
    settings_id: int

    class Config:
        from_attributes = True


class DriverUpdateLocation(BaseModel):
    lat: float
    lng: float


class OrderCreate(BaseModel):
    client_name: str
    client_phone: str
    pickup_address: str
    delivery_address: str
    pickup_lat: float
    pickup_lng: float
    delivery_lat: float
    delivery_lng: float
    settings_id: int


class OrderResponse(BaseModel):
    id: int
    client_name: str
    client_phone: str
    pickup_address: str
    delivery_address: str
    status: OrderStatus
    driver_id: Optional[int]
    created_at: datetime
    settings_id: int

    class Config:
        from_attributes = True


class OrderAccept(BaseModel):
    driver_id: int

class OrderReject(BaseModel):
    driver_id: int


class OrderComplete(BaseModel):
    driver_id: int


class AlgorithmResponse(BaseModel):
    algorithm: DistributionAlgorithm


class FactorResponse(BaseModel):
    factor: float


class AlgorithmUpdate(BaseModel):
    algorithm: DistributionAlgorithm

class TariffCreate(BaseModel):
    name: str
    min_cost: float = 0.0
    min_km: float = 0.0
    min_minutes: float = 0.0
    price_per_km: float = 0.0
    price_per_min: float = 0.0
    waiting_price_per_min: float = 5.0
    free_waiting_minutes: float = 2.0
    min_speed_kmh: int = 0
    double_tariff_speed: int = 100
    country_price_per_km: float = 5.0
    country_price_per_min: float = 5.0
    is_active: bool = True
    distance_and_time: bool = True


class TariffResponse(BaseModel):
    id: int
    name: str
    min_cost: float
    min_km: float
    min_minutes: float
    price_per_km: float
    price_per_min: float
    waiting_price_per_min: float
    free_waiting_minutes: float
    min_speed_kmh: int
    double_tariff_speed: int
    country_price_per_km: float
    country_price_per_min: float
    is_active: bool
    distance_and_time: bool

    class Config:
        from_attributes = True