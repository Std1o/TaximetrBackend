from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException

from taximetr.database import get_session
from taximetr.model.enums import DistributionAlgorithm
from taximetr.model.schemas import SettingsCreate
from taximetr.tables import Settings


class SettingsService:

    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def add_settings(self, settings_create: SettingsCreate):
        settings = Settings()
        settings.region = settings_create.region
        settings.card = settings_create.card
        settings.locality = settings_create.locality
        settings.name = settings_create.name
        self.session.add(settings)
        self.session.commit()
        self.session.refresh(settings)
        return settings

    def get_all_settings(self) -> Settings:
        settings = self.session.query(Settings).all()
        return settings

    def get_settings(self, settings_id: int) -> Settings:
        settings = self.session.query(Settings).filter_by(id=settings_id).first()
        return settings

    def update_algorithm(self, settings_id: int, algorithm: DistributionAlgorithm):
        settings = self.get_settings(settings_id)
        settings.algorithm = algorithm.value
        self.session.commit()
        self.session.refresh(settings)

    def update_factor(self, settings_id: int, factor: float):
        settings = self.get_settings(settings_id)
        settings.factor = factor
        self.session.commit()
        self.session.refresh(settings)

    def update_payment(self, settings_id: int, payment: int):
        settings = self.get_settings(settings_id)
        settings.payment = payment
        self.session.commit()
        self.session.refresh(settings)

    def get_algorithm(self, settings_id: int) -> DistributionAlgorithm:
        settings = self.get_settings(settings_id)
        return DistributionAlgorithm(settings.algorithm)

    def update_percent(self, settings_id: int, percent: int):
        settings = self.get_settings(settings_id)
        settings.percent = percent
        self.session.commit()
        self.session.refresh(settings)

    def update_shift_price(self, settings_id: int, hours: int, price: int):
        settings = self.get_settings(settings_id)

        if hours == 1:
            settings.price_1_hour = price
        elif hours == 2:
            settings.price_2_hours = price
        elif hours == 8:
            settings.price_8_hours = price
        elif hours == 24:
            settings.price_24_hours = price
        elif hours == 720:  # 30 дней * 24 часа
            settings.price_1_month = price
        else:
            raise HTTPException(status_code=400, detail="Invalid hours. Allowed: 1, 2, 8, 24, 720")

        self.session.commit()
        self.session.refresh(settings)