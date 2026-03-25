from fastapi import APIRouter, Depends
import asyncio

from taximetr.model.schemas import AlgorithmUpdate, SettingsResponse
from taximetr.service.settings_service import SettingsService
from taximetr.service.websocket_manager import manager

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/")
def get_settings(service: SettingsService = Depends()):
    settings = service.get_settings()
    return settings


@router.put("/algorithm", response_model=SettingsResponse)
async def update_algorithm(
        algorithm_update: AlgorithmUpdate,
        service: SettingsService = Depends()
):
    service.update_algorithm(algorithm_update.algorithm)

    asyncio.create_task(manager.broadcast_to_drivers({
        "type": "algorithm_changed",
        "algorithm": algorithm_update.algorithm.value
    }))

    return SettingsResponse(algorithm=algorithm_update.algorithm)