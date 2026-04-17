from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import Depends

from taximetr.database import get_session
from taximetr.model.schemas import TariffCreate
from taximetr.tables import Tariff


class TariffService:

    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def create_tariff(self, tariff_data: TariffCreate) -> Tariff:
        tariff = Tariff(**tariff_data.model_dump())
        self.session.add(tariff)
        self.session.commit()
        self.session.refresh(tariff)
        return tariff

    def get_all_tariffs(self, settings_id: int) -> List[Tariff]:
        return self.session.query(Tariff).filter_by(settings_id=settings_id).all()

    def get_tariff(self, tariff_id: int) -> Optional[Tariff]:
        return self.session.query(Tariff).filter(Tariff.id == tariff_id).first()

    def update_tariff(self, tariff_id: int, tariff_data: TariffCreate) -> Optional[Tariff]:
        tariff = self.get_tariff(tariff_id)
        if tariff:
            for key, value in tariff_data.model_dump().items():
                setattr(tariff, key, value)
            self.session.commit()
            self.session.refresh(tariff)
        return tariff

    def delete_tariff(self, tariff_id: int) -> bool:
        tariff = self.get_tariff(tariff_id)
        if tariff:
            self.session.delete(tariff)
            self.session.commit()
            return True
        return False