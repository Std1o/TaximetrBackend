from fastapi import APIRouter, Depends
import asyncio

from taximetr.model.schemas import AlgorithmUpdate, AlgorithmResponse, FactorResponse
from taximetr.service.settings_service import SettingsService
from taximetr.service.websocket_manager import manager

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/")
def get_settings(service: SettingsService = Depends()):
    settings = service.get_settings()
    return settings


@router.put("/algorithm", response_model=AlgorithmResponse)
async def update_algorithm(
        algorithm_update: AlgorithmUpdate,
        service: SettingsService = Depends()
):
    service.update_algorithm(algorithm_update.algorithm)
    return AlgorithmResponse(algorithm=algorithm_update.algorithm)

@router.put("/factor", response_model=FactorResponse)
async def update_algorithm(
        factor: float,
        service: SettingsService = Depends()
):
    service.update_factor(factor)
    return FactorResponse(factor=factor)