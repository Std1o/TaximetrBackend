from fastapi import APIRouter, Depends
import asyncio

from taximetr.model.schemas import AlgorithmUpdate, AlgorithmResponse, FactorResponse
from taximetr.service.settings_service import SettingsService
from taximetr.service.websocket_manager import manager

router = APIRouter(prefix="/settings", tags=["settings"])

@router.post("/")
def add_settings(region: str, service: SettingsService = Depends()):
    settings = service.add_settings(region)
    return settings

@router.get("/")
def get_settings(settings_id: int, service: SettingsService = Depends()):
    settings = service.get_settings(settings_id)
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
async def update_algorithm(
        settings_id: int,
        factor: float,
        service: SettingsService = Depends()
):
    service.update_factor(settings_id, factor)
    return FactorResponse(factor=factor)