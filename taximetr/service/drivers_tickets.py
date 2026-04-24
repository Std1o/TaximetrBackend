import sys
from datetime import datetime, timedelta
from typing import List

from dateutil.relativedelta import relativedelta
from fastapi import Depends
from sqlalchemy import select

from taximetr import tables
from taximetr.database import Session, get_session
from taximetr.model.tickets import Ticket

def debug_print(*args, **kwargs):
    print(*args, **kwargs, file=sys.stderr, flush=True)


class TicketService:
    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    async def get_tickets(self) -> List[Ticket]:
        statement = select(tables.DriversTickets)
        return self.session.execute(statement).scalars().all()

    async def get_my_tickets(self, user_id: int) -> List[Ticket]:
        statement = select(tables.DriversTickets).filter_by(user_id = user_id)
        return self.session.execute(statement).scalars().all()

    async def create_ticket(self, ticket: Ticket) -> Ticket:
        new_ticket = tables.DriversTickets(
            user_id=ticket.user_id,
            username=ticket.username,
            phone=ticket.phone,
            image_url=ticket.image_url,
            debt = ticket.debt
        )
        self.session.add(new_ticket)
        self.session.commit()

        return ticket

    async def get_user_by_phone(self, phone: str) -> tables.User:
        statement = select(tables.User).filter_by(phone=phone)
        return self.session.execute(statement).scalars().first()

    async def get_ticket_by_phone(self, phone: str) -> tables.DriversTickets:
        statement = select(tables.DriversTickets).filter_by(phone=phone)
        return self.session.execute(statement).scalars().first()

    async def give_premium(self, phone: str):
        user = await self.get_user_by_phone(phone)
        user.premium = datetime.now() + relativedelta(day=1)
        debug_print(f"now: {datetime.now()}")
        debug_print(f"result: {datetime.now() + relativedelta(day=1)}")
        self.session.commit()
        ticket = await self.get_ticket_by_phone(phone)
        self.session.delete(ticket)
        self.session.commit()
        return await self.get_tickets()

    async def reject_premium(self, phone: str):
        ticket = await self.get_ticket_by_phone(phone)
        self.session.delete(ticket)
        self.session.commit()
        return await self.get_tickets()