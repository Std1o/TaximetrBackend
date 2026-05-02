import sys

from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import Depends
from datetime import datetime

from taximetr.database import get_session
from taximetr.model.enums import OrderStatus
from taximetr.model.schemas import OrderCreate, OrderResponse
from taximetr.tables import Order, Driver


def debug_print(*args, **kwargs):
    print(*args, **kwargs, file=sys.stderr, flush=True)

class OrderService:

    def __init__(self, db: Session = Depends(get_session)):
        self.db = db

    def create_order(self, order_data: OrderCreate) -> Order:
        order = Order(**order_data.model_dump())
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        return order

    def get_all_orders(self, settings_id: int) -> List[Order]:
        return self.db.query(Order).filter_by(settings_id=settings_id).order_by(Order.created_at.desc()).all()

    def get_orders_for_current_month(self, settings_id: int) -> List[dict]:
        from datetime import datetime

        now = datetime.now()
        start_date = datetime(now.year, now.month, 1)

        if now.month == 12:
            end_date = datetime(now.year + 1, 1, 1)
        else:
            end_date = datetime(now.year, now.month + 1, 1)

        results = self.db.query(
            Order.id,
            Order.client_name,
            Order.client_phone,
            Order.pickup_address,
            Order.delivery_address,
            Order.status,
            Order.price,
            Order.created_at,
            Order.completed_at,
            Driver.name,
            Driver.phone
        ).outerjoin(
            Driver, Order.driver_id == Driver.id
        ).filter(
            Order.settings_id == settings_id,
            Order.created_at >= start_date,
            Order.created_at < end_date
        ).order_by(
            Order.created_at.asc()
        ).all()

        return [
            {
                "id": row.id,
                "client_name": row.client_name,
                "client_phone": row.client_phone,
                "pickup_address": row.pickup_address,
                "delivery_address": row.delivery_address,
                "status": row.status,
                "price": row.price,
                "created_at": row.created_at,
                "completed_at": row.completed_at,
                "driver_name": row.name,
                "driver_phone": row.phone
            }
            for row in results
        ]

    def get_table_order(self, order_id: int) -> Optional[Order]:
        return self.db.query(Order).filter(Order.id == order_id).first()

    def get_order(self, order_id: int) -> Optional[OrderResponse]:
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if order:
            return OrderResponse.model_validate(order)
        return None

    def accept_order(self, order_id: int, driver_id: int) -> Optional[Order]:
        order = self.get_table_order(order_id)
        if not order:
            return None

        debug_print(order.status)
        if order.status != OrderStatus.PENDING.value:
            raise ValueError(f"Order {order_id} is not pending")

        order.status = OrderStatus.ACCEPTED.value
        order.driver_id = driver_id
        order.accepted_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(order)
        return order

    def reject_order(self, order_id: int, driver_id: int) -> Optional[Order]:
        """Водитель отказался от заказа"""
        order = self.get_table_order(order_id)
        if not order:
            return None

        if order.status != OrderStatus.PENDING.value:
            raise ValueError(f"Order {order_id} is not pending")

        # Помечаем как отклоненный этим водителем
        order.status = OrderStatus.REJECTED.value
        order.driver_id = driver_id

        self.db.commit()
        self.db.refresh(order)
        return order

    def complete_order(self, order_id: int, driver_id: int) -> Optional[Order]:
        order = self.get_table_order(order_id)
        if not order:
            return None

        if order.driver_id != driver_id:
            raise ValueError(f"Order {order_id} is not assigned to driver {driver_id}")

        order.status = OrderStatus.COMPLETED.value
        order.completed_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(order)
        return order

    def update_status(self, order_id: int, status: str) -> Optional[Order]:
        order = self.get_table_order(order_id)
        if order:
            order.status = status
            if status == OrderStatus.COMPLETED.value:
                order.completed_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(order)
        return order

    def cancel_order(self, order_id: int) -> Optional[Order]:
        """Отмена заказа"""
        order = self.get_table_order(order_id)
        if order and order.status in [OrderStatus.PENDING.value, OrderStatus.ACCEPTED.value]:
            order.status = OrderStatus.CANCELLED.value
            self.db.commit()
            self.db.refresh(order)
        return order

    def set_order_price(self, order_id: int, price: float) -> Optional[Order]:
        order = self.get_table_order(order_id)
        if order:
            order.price = price  # нужно добавить поле price в таблицу Order
            self.db.commit()
            self.db.refresh(order)
        return order