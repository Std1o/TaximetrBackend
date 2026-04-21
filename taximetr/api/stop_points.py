from typing import List

from fastapi import APIRouter, Depends

from taximetr import tables
from taximetr.model.schemas import DriverResponse, StopPointCreate, StopPoint
from taximetr.service.stop_points import StopPointsService

router = APIRouter(prefix="/stop_points", tags=["stop_points"])


@router.post("/", response_model=StopPoint)
def create_stop_point(
        stop_point: StopPointCreate,
        service: StopPointsService = Depends(),
):
    return service.create(stop_point)


@router.get("/", response_model=List[StopPoint])
def get_stop_points(order_id: int, service: StopPointsService = Depends()):
    return service.get_stop_points(order_id)


@router.delete("/{stop_point_id}")
def delete_stop_point(stop_point_id: int, service: StopPointsService = Depends()):
    service.delete_stop_point(stop_point_id)
