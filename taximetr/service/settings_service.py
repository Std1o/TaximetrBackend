from sqlalchemy.orm import Session
from fastapi import Depends

from taximetr.database import get_session
from taximetr.model.enums import DistributionAlgorithm
from taximetr.tables import Settings


class SettingsService:

    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def add_settings(self, region: str):
        settings = Settings()
        settings.region = region
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
        settings.distribution_algorithm = algorithm.value
        self.session.commit()
        self.session.refresh(settings)

    def update_factor(self, settings_id: int, factor: float):
        settings = self.get_settings(settings_id)
        settings.factor = factor
        self.session.commit()
        self.session.refresh(settings)

    def get_algorithm(self, settings_id: int) -> DistributionAlgorithm:
        settings = self.get_settings(settings_id)
        return DistributionAlgorithm(settings.algorithm)

