from typing import List

from fastapi import APIRouter, Depends

from taximetr import tables
from taximetr.model.auth import User
from taximetr.model.schemas import Ticket
from taximetr.service.auth import get_current_user
from taximetr.service.premium import PremiumService
from taximetr.service.ticket import TicketService

router = APIRouter(prefix='/premium', tags=["premium"])


@router.post("/")
async def create(
        settings_id: int,
        sum: int,
        card: str,
        service: PremiumService = Depends()
):
     return await service.create(settings_id, sum, card)

@router.get('/')
async def get(settings_id: int, service: PremiumService = Depends()):
    return await service.get_premium(settings_id)