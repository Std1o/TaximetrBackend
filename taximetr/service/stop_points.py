from typing import List, Optional

from fastapi import Depends
from sqlalchemy.orm import Session

from taximetr import tables
from taximetr.database import get_session
from taximetr.model.schemas import StopPointCreate


class StopPointsService:

    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def create(self, stop_point_create: StopPointCreate) -> tables.StopPoints:
        point = tables.StopPoints(
            order_id=stop_point_create.order_id,
            address=stop_point_create.address
        )
        self.session.add(point)
        self.session.commit()
        self.session.refresh(point)

        return point

    def get_stop_point(self, stop_point_id: int) -> Optional[tables.StopPoints]:
        return self.session.query(tables.StopPoints).filter(tables.StopPoints.id == stop_point_id).first()

    def get_stop_points(self, order_id: int) -> List[tables.StopPoints]:
        return self.session.query(tables.StopPoints).filter(tables.StopPoints.order_id == order_id).all()

    def delete_stop_point(self, stop_point_id: int):
        stop_point = self.get_stop_point(stop_point_id)
        self.session.delete(stop_point)
        self.session.commit()