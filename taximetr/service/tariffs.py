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

    def get_all_tariffs(self) -> List[Tariff]:
        return self.session.query(Tariff).all()

    def get_tariff(self, tariff_id: int) -> Optional[Tariff]:
        return self.session.query(Tariff).filter(Tariff.id == tariff_id).first()

    def get_active_tariff(self) -> Optional[Tariff]:
        return self.session.query(Tariff).filter(Tariff.is_active == True).first()

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

    def init_default_tariffs(self):
        """Создание базовых тарифов при инициализации"""
        if self.session.query(Tariff).count() == 0:
            default_tariffs = [
                Tariff(
                    name="Километровый",
                    min_cost=0.0,
                    min_km=0.0,
                    min_minutes=0.0,
                    price_per_km=10.0,
                    price_per_min=0.0,
                    waiting_price_per_min=5.0,
                    free_waiting_minutes=2.0,
                    min_speed_kmh=0,
                    double_tariff_speed=100,
                    country_price_per_km=5.0,
                    country_price_per_min=5.0,
                    is_active=True,
                    distance_and_time=True
                ),
                Tariff(
                    name="Повременной",
                    min_cost=0.0,
                    min_km=0.0,
                    min_minutes=0.0,
                    price_per_km=0.0,
                    price_per_min=10.0,
                    waiting_price_per_min=5.0,
                    free_waiting_minutes=2.0,
                    min_speed_kmh=0,
                    double_tariff_speed=100,
                    country_price_per_km=5.0,
                    country_price_per_min=5.0,
                    is_active=True,
                    distance_and_time=True
                ),
                Tariff(
                    name="Пробег ИЛИ Простой",
                    min_cost=0.0,
                    min_km=0.0,
                    min_minutes=0.0,
                    price_per_km=10.0,
                    price_per_min=5.0,
                    waiting_price_per_min=5.0,
                    free_waiting_minutes=2.0,
                    min_speed_kmh=0,
                    double_tariff_speed=100,
                    country_price_per_km=5.0,
                    country_price_per_min=5.0,
                    is_active=True,
                    distance_and_time=False
                ),
                Tariff(
                    name="Пробег и Время",
                    min_cost=0.0,
                    min_km=0.0,
                    min_minutes=0.0,
                    price_per_km=7.0,
                    price_per_min=7.0,
                    waiting_price_per_min=5.0,
                    free_waiting_minutes=2.0,
                    min_speed_kmh=0,
                    double_tariff_speed=100,
                    country_price_per_km=5.0,
                    country_price_per_min=5.0,
                    is_active=True,
                    distance_and_time=True
                )
            ]

            for tariff in default_tariffs:
                self.session.add(tariff)
            self.session.commit()