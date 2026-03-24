from fastapi import APIRouter, Depends, HTTPException
from typing import List

from taximetr.model.schemas import DriverResponse, DriverCreate, DriverUpdateLocation
from taximetr.service.driver_service import DriverService

router = APIRouter(prefix="/drivers", tags=["drivers"])

@router.post("/", response_model=DriverResponse)
def create_driver(driver: DriverCreate, service: DriverService = Depends()):
    try:
        return service.create_driver(driver)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[DriverResponse])
def get_drivers(service: DriverService = Depends()):
    return service.get_all_drivers()

@router.get("/{driver_id}", response_model=DriverResponse)
def get_driver(driver_id: int, service: DriverService = Depends()):
    driver = service.get_driver(driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver

@router.put("/{driver_id}/location")
def update_location(
    driver_id: int,
    location: DriverUpdateLocation,
    service: DriverService = Depends()
):
    driver = service.update_location(driver_id, location)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
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