from datetime import datetime
from typing import List, Optional
from fastapi import Depends, HTTPException

from taximetr.database import Session, get_session
from taximetr.model.schemas import CarCreate, CarUpdate
from taximetr.tables import Car, Driver


class CarService:
    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def _get_driver(self, driver_id: int) -> Driver:
        """Вспомогательный метод для получения водителя"""
        driver = self.session.query(Driver).filter(Driver.id == driver_id).first()
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")
        return driver

    def get_car(self, car_id: int) -> Car:
        car = self.session.query(Car).filter(Car.id == car_id).first()
        if not car:
            raise HTTPException(status_code=404, detail="Car not found")
        return car

    def add_car(self, driver_id: int, car_data: CarCreate) -> Car:
        # Проверяем, что водитель существует
        driver = self._get_driver(driver_id)

        # Проверяем, что водитель одобрен
        if not driver.is_approved:
            raise HTTPException(status_code=403, detail="Driver not approved")

        car = Car(driver_id=driver_id, **car_data.model_dump(), is_approved=False)
        self.session.add(car)
        self.session.commit()
        self.session.refresh(car)
        return car

    def get_driver_cars(self, driver_id: int) -> List[Car]:
        # Проверяем, что водитель существует
        self._get_driver(driver_id)
        return self.session.query(Car).filter(Car.driver_id == driver_id).all()

    def update_car(self, car_id: int, car_data: CarUpdate) -> Optional[Car]:
        car = self.session.query(Car).filter(Car.id == car_id).first()
        if car:
            for key, value in car_data.model_dump(exclude_unset=True).items():
                setattr(car, key, value)
            self.session.commit()
            self.session.refresh(car)
        return car

    def delete_car(self, car_id: int) -> bool:
        car = self.session.query(Car).filter(Car.id == car_id).first()
        if car:
            self.session.delete(car)
            self.session.commit()
            return True
        return False

    def approve_car(self, car_id: int, approved: bool) -> Optional[Car]:
        """Одобрить машину"""
        car = self.session.query(Car).filter(Car.id == car_id).first()
        if not car:
            return None
        if approved:
            car.is_approved = True
            car.approved_at = datetime.utcnow()
            self.session.commit()
            self.session.refresh(car)
            return car
        else:
            # Если не одобрили - удаляем
            self.session.delete(car)
            self.session.commit()
            return None

    def get_pending_cars(self, settings_id: int) -> List[Car]:
        """Машины, ожидающие одобрения"""
        return self.session.query(Car).join(Driver).filter(
            Car.is_approved == False,
            Driver.settings_id == settings_id
        ).all()