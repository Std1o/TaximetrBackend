from sqlalchemy.orm import Session
from fastapi import Depends

from taximetr.database import get_session
from taximetr.model.enums import DistributionAlgorithm
from taximetr.tables import Settings


class SettingsService:

    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def get_settings(self) -> Settings:
        settings = self.session.query(Settings).first()
        if not settings:
            settings = Settings()
            self.session.add(settings)
            self.session.commit()
            self.session.refresh(settings)
        return settings

    def update_algorithm(self, algorithm: DistributionAlgorithm):
        settings = self.get_settings()
        settings.distribution_algorithm = algorithm.value
        self.session.commit()
        self.session.refresh(settings)

    def get_algorithm(self) -> DistributionAlgorithm:
        settings = self.get_settings()
        return DistributionAlgorithm(settings.distribution_algorithm)