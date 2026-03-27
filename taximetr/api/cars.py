from typing import List

from fastapi import APIRouter, Depends

from taximetr.model.schemas import CarResponse, CarCreate, CarUpdate
from taximetr.service.car_service import CarService

router = APIRouter(prefix="/cars", tags=["cars"])

@router.post("/", response_model=CarResponse)
def add_car(car: CarCreate, driver_id: int, service: CarService = Depends()):
    return service.add_car(driver_id, car)

@router.get("/driver/{driver_id}", response_model=List[CarResponse])
def get_driver_cars(driver_id: int, service: CarService = Depends()):
    return service.get_driver_cars(driver_id)

@router.put("/{car_id}", response_model=CarResponse)
def update_car(car_id: int, car: CarUpdate, service: CarService = Depends()):
    return service.update_car(car_id, car)

@router.delete("/{car_id}")
def delete_car(car_id: int, service: CarService = Depends()):
    service.delete_car(car_id)
    return {"message": "Car deleted"}