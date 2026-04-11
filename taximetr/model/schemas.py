from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from taximetr.model.enums import DriverStatus, OrderStatus, DistributionAlgorithm


class CarCreate(BaseModel):
    brand: str
    model: str
    color: str
    license_plate: str

class CarResponse(BaseModel):
    id: int
    driver_id: int
    brand: str
    model: str
    color: str
    license_plate: str
    is_approved: bool
    created_at: datetime
    approved_at: Optional[datetime]

    class Config:
        from_attributes = True

class DriverCreate(BaseModel):
    user_id: Optional[int]
    name: str
    phone: str
    license_photo: Optional[str] = None
    settings_id: int
    cars: List[CarCreate] = Field(default_factory=list) # машины при регистрации

class DriverResponse(BaseModel):
    id: int
    user_id: int
    name: str
    phone: str
    license_photo: Optional[str]
    is_approved: bool
    status: DriverStatus
    current_lat: float
    current_lng: float
    current_order_id: Optional[int]
    settings_id: int
    cars: List[CarResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True

class DriverUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    license_photo: Optional[str] = None

class CarUpdate(BaseModel):
    brand: Optional[str] = None
    model: Optional[str] = None
    color: Optional[str] = None
    license_plate: Optional[str] = None


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
    price: float

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class OrderAccept(BaseModel):
    driver_id: int

class OrderReject(BaseModel):
    driver_id: int
    reason: str


class OrderComplete(BaseModel):
    driver_id: int


class AlgorithmResponse(BaseModel):
    algorithm: DistributionAlgorithm


class FactorResponse(BaseModel):
    factor: float

class PaymentResponse(BaseModel):
    payment: int


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

class OrderPrice(BaseModel):
    driver_id: int
    price: float

class SettingsCreate(BaseModel):
    region: str
    card: str

class Ticket(BaseModel):
    user_id: int
    username: str
    phone: str
    image_url: str

    class Config:
        from_attributes = True