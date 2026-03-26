from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import Depends

from taximetr.database import get_session
from taximetr.model.enums import DriverStatus
from taximetr.model.schemas import DriverCreate, DriverUpdateLocation
from taximetr.tables import Driver


class DriverService:

    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def create_driver(self, driver_data: DriverCreate) -> Driver:

        driver = Driver(**driver_data.model_dump())
        self.session.add(driver)
        self.session.commit()
        self.session.refresh(driver)
        return driver

    def get_all_drivers(self) -> List[Driver]:
        return self.session.query(Driver).all()

    def get_driver(self, driver_id: int) -> Optional[Driver]:
        return self.session.query(Driver).filter(Driver.id == driver_id).first()

    def update_location(self, driver_id: int, location: DriverUpdateLocation) -> Optional[Driver]:
        driver = self.get_driver(driver_id)
        if driver:
            driver.current_lat = location.lat
            driver.current_lng = location.lng
            self.session.commit()
            self.session.refresh(driver)
        return driver

    def set_busy(self, driver_id: int, order_id: int) -> Optional[Driver]:
        driver = self.get_driver(driver_id)
        if driver:
            driver.status = DriverStatus.BUSY.value
            driver.current_order_id = order_id
            self.session.commit()
            self.session.refresh(driver)
        return driver

    def set_online(self, driver_id: int) -> Optional[Driver]:
        driver = self.get_driver(driver_id)
        if driver:
            driver.status = DriverStatus.ONLINE.value
            driver.current_order_id = None
            self.session.commit()
            self.session.refresh(driver)
        return driver

    def set_offline(self, driver_id: int) -> Optional[Driver]:
        driver = self.get_driver(driver_id)
        if driver:
            driver.status = DriverStatus.OFFLINE.value
            driver.current_order_id = None
            self.session.commit()
            self.session.refresh(driver)
        return driver

    def get_online_drivers(self, settings_id: int) -> List[Driver]:
        return self.session.query(Driver).filter(
            Driver.status == DriverStatus.ONLINE.value,
            Driver.settings_id == settings_id
        ).order_by(Driver.id).all()