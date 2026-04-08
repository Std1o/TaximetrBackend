from fastapi import APIRouter, Depends, HTTPException
from typing import List
import asyncio

from taximetr.service.websocket_manager import manager
from taximetr.service.auth import get_current_user
from taximetr.tables import User, Driver
from taximetr.service.driver_service import DriverService
from taximetr.service.order_service import OrderService

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post("/drivers/all")
async def notify_all_drivers(
        title: str,
        body: str,
        settings_id: int,
        current_user: User = Depends(get_current_user)
):
    """Отправить уведомление всем водителям в регионе"""

    await manager.broadcast_to_drivers({
        "type": "push_notification",
        "title": title,
        "body": body,
        "sender": current_user.username
    }, settings_id=settings_id)

    return {"message": f"Notification sent to all drivers in region {settings_id}"}


@router.post("/drivers/{driver_id}")
async def notify_driver(
        driver_id: int,
        title: str,
        body: str,
        current_user: User = Depends(get_current_user),
        driver_service: DriverService = Depends()
):
    """Отправить уведомление конкретному водителю"""

    driver = driver_service.get_driver(driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    await manager.send_to_driver(driver_id, {
        "type": "push_notification",
        "title": title,
        "body": body,
        "sender": current_user.username
    }, factor=None)

    return {"message": f"Notification sent to driver {driver_id}"}


@router.post("/clients/all")
async def notify_all_clients(
        title: str,
        body: str,
        settings_id: int,
        current_user: User = Depends(get_current_user)
):
    """Отправить уведомление всем клиентам в регионе"""

    # Нужно хранить клиентские соединения в manager
    await manager.broadcast_to_clients({
        "type": "push_notification",
        "title": title,
        "body": body,
        "sender": current_user.username
    }, settings_id=settings_id)

    return {"message": f"Notification sent to all clients in region {settings_id}"}


@router.post("/orders/{order_id}/client")
async def notify_order_client(
        order_id: int,
        title: str,
        body: str,
        current_user: User = Depends(get_current_user),
        order_service: OrderService = Depends()
):
    """Отправить уведомление клиенту конкретного заказа"""

    order = order_service.get_table_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    await manager.send_to_order(order_id, {
        "type": "push_notification",
        "title": title,
        "body": body,
        "sender": current_user.username
    })

    return {"message": f"Notification sent to client of order {order_id}"}