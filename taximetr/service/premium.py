from datetime import datetime, timedelta
from typing import List

from dateutil.relativedelta import relativedelta
from fastapi import Depends
from sqlalchemy import select

from taximetr import tables
from taximetr.database import Session, get_session
from taximetr.model.schemas import Ticket


class PremiumService:
    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    async def get_premium(self, settings_id: int) -> tables.Premium:
        statement = select(tables.Premium).filter_by(settings_id=settings_id)
        return self.session.execute(statement).scalars().first()

    async def create(self, settings_id: int, sum: int, card: str) -> tables.Premium:
        new_premium = tables.Premium(
            settings_id=settings_id,
            sum=sum,
            card=card
        )
        self.session.add(new_premium)
        self.session.commit()
        self.session.refresh(new_premium)

        return new_premium

    async def update(self, settings_id: int, sum: int, card: str):
        premium = await self.get_premium(settings_id)
        premium.sum = sum
        premium.card = card
        self.session.commit()
        self.session.refresh(premium)
        return premium