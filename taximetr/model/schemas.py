from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from taximetr.model.enums import DriverStatus, OrderStatus, DistributionAlgorithm


class DriverCreate(BaseModel):
    name: str
    phone: str


class DriverResponse(BaseModel):
    id: int
    name: str
    phone: str
    status: DriverStatus
    current_lat: float
    current_lng: float
    current_order_id: Optional[int]

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


class OrderResponse(BaseModel):
    id: int
    client_name: str
    client_phone: str
    pickup_address: str
    delivery_address: str
    status: OrderStatus
    driver_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class OrderAccept(BaseModel):
    driver_id: int

class OrderReject(BaseModel):
    driver_id: int


class OrderComplete(BaseModel):
    driver_id: int


class SettingsResponse(BaseModel):
    algorithm: DistributionAlgorithm


class SettingsUpdate(BaseModel):
    algorithm: DistributionAlgorithm