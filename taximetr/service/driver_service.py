from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import Depends

from taximetr.database import get_session
from taximetr.model.enums import DriverStatus
from taximetr.model.schemas import DriverCreate, DriverUpdateLocation
from taximetr.tables import Driver, Car
from taximetr.service.websocket_manager import manager


class DriverService:

    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def create_driver(self, driver_data: DriverCreate) -> Driver:
        driver = Driver(
            user_id=driver_data.user_id,
            name=driver_data.name,
            phone=driver_data.phone,
            license_photo=driver_data.license_photo,
            is_approved=False,
            settings_id=driver_data.settings_id
        )
        self.session.add(driver)
        self.session.commit()
        self.session.refresh(driver)

        # Машины тоже ждут одобрения
        for car_data in driver_data.cars:
            car = Car(driver_id=driver.id, **car_data.model_dump(), is_approved=False)
            self.session.add(car)
        self.session.commit()

        return driver

    def approve_driver(self, driver_id: int, approved: bool) -> Optional[Driver]:
        driver = self.get_driver(driver_id)
        if not driver:
            return None

        if approved:
            driver.is_approved = True
            self.session.commit()
            self.session.refresh(driver)
            return driver
        else:
            # Если не одобрили - удаляем
            for car in driver.cars:
                self.session.delete(car)
            self.session.delete(driver)
            self.session.commit()
            return None

    def get_pending_drivers(self, settings_id: int) -> List[Driver]:
        return self.session.query(Driver).filter(
            Driver.is_approved == False,
            Driver.settings_id == settings_id
        ).all()

    def get_approved_drivers(self, settings_id: int) -> List[Driver]:
        return self.session.query(Driver).filter(
            Driver.is_approved == True,
            Driver.settings_id == settings_id
        ).all()

    def get_all_drivers(self, settings_id) -> List[Driver]:
        return self.session.query(Driver).filter_by(settings_id=settings_id).all()

    def get_driver(self, driver_id: int) -> Optional[Driver]:
        return self.session.query(Driver).filter(Driver.id == driver_id).first()

    def get_driver_by_user_id(self, user_id: int) -> Optional[Driver]:
        return self.session.query(Driver).filter(Driver.user_id == user_id).first()

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
            print(f"🔴 set_online: вызываю _broadcast_queue_update для settings_id={driver.settings_id}", flush=True)
            driver.status = DriverStatus.ONLINE.value
            driver.current_order_id = None
            self.session.commit()
            self.session.refresh(driver)

            # 👇 ОБНОВЛЯЕМ ОЧЕРЕДЬ
            self._broadcast_queue_update(driver.settings_id)

        return driver

    def set_offline(self, driver_id: int) -> Optional[Driver]:
        driver = self.get_driver(driver_id)
        if driver:
            driver.status = DriverStatus.OFFLINE.value
            driver.current_order_id = None
            self.session.commit()
            self.session.refresh(driver)

            # 👇 ОБНОВЛЯЕМ ОЧЕРЕДЬ
            self._broadcast_queue_update(driver.settings_id)

        return driver

    def delete_driver(self, driver_id: int):
        driver = self.get_driver(driver_id)
        self.session.delete(driver)
        self.session.commit()

    def get_online_drivers(self, settings_id: int) -> List[Driver]:
        return self.session.query(Driver).filter(
            Driver.status == DriverStatus.ONLINE.value,
            Driver.settings_id == settings_id,
            Driver.is_approved == True,
            Driver.cars.any(Car.is_approved == True)  # Если связь настроена
        ).order_by(Driver.id).all()

    # 👇 НОВЫЙ МЕТОД ДЛЯ ОБНОВЛЕНИЯ ОЧЕРЕДИ
    def _broadcast_queue_update(self, settings_id: int):
        print(f"🔴 _broadcast_queue_update ВЫЗВАН для settings_id={settings_id}", flush=True)
        """Отправить обновление очереди всем подключенным клиентам"""
        from taximetr.service.distributor import distributor
        distributor._broadcast_queue_update(settings_id)