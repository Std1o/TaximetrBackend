from fastapi import APIRouter, Depends, HTTPException
from typing import List
import asyncio

from taximetr.model.enums import OrderStatus
from taximetr.model.schemas import OrderCreate, OrderResponse, OrderAccept, OrderReject, OrderComplete
from taximetr.service.distributor import distributor
from taximetr.service.driver_service import DriverService
from taximetr.service.order_service import OrderService
from taximetr.service.settings_service import SettingsService
from taximetr.service.websocket_manager import manager

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/", response_model=OrderResponse)
async def create_order(
        order: OrderCreate,
        order_service: OrderService = Depends(),
        driver_service: DriverService = Depends()
):
    db_order = order_service.create_order(order)
    asyncio.create_task(distributor.distribute_order(db_order, order_service.db))
    return db_order


@router.get("/", response_model=List[OrderResponse])
def get_orders(service: OrderService = Depends()):
    return service.get_all_orders()


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, service: OrderService = Depends()):
    order = service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.put("/{order_id}/accept")
async def accept_order(
        order_id: int,
        data: OrderAccept,
        order_service: OrderService = Depends(),
        driver_service: DriverService = Depends(),
        settings_service: SettingsService = Depends()
):
    order = order_service.get_order(order_id)
    factor = settings_service.get_settings().factor
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    driver = driver_service.get_driver(data.driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    try:
        order = order_service.accept_order(order_id, data.driver_id)
        driver_service.set_busy(data.driver_id, order_id)

        # Уведомляем всех водителей
        asyncio.create_task(manager.broadcast_to_drivers({
            "type": "order_accepted",
            "order_id": order_id,
            "driver_id": data.driver_id,
            "driver_name": driver.name
        }, factor=factor))

        # Уведомляем клиента через вебсокет заказа
        asyncio.create_task(manager.send_to_order(order_id, {
            "type": "order_accepted",
            "driver_id": data.driver_id,
            "driver_name": driver.name,
            "driver_phone": driver.phone,
            "lat": driver.current_lat,
            "lng": driver.current_lng,
        }))

        return {"message": "Order accepted", "order_id": order_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{order_id}/reject")
async def reject_order(
        order_id: int,
        data: OrderReject,
        order_service: OrderService = Depends(),
        driver_service: DriverService = Depends()
):
    order = order_service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    driver = driver_service.get_driver(data.driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    try:
        order = order_service.reject_order(order_id, data.driver_id)

        # Уведомляем клиента
        asyncio.create_task(manager.send_to_order(order_id, {
            "type": "order_rejected",
            "driver_id": data.driver_id,
            "message": "Driver rejected the order"
        }))

        # Перераспределяем заказ
        asyncio.create_task(distributor.redistribute_order(order, order_service, data.driver_id))

        return {"message": "Order rejected", "order_id": order_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{order_id}/complete")
async def complete_order(
        order_id: int,
        data: OrderComplete,
        order_service: OrderService = Depends(),
        driver_service: DriverService = Depends()
):
    try:
        order = order_service.complete_order(order_id, data.driver_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        driver_service.set_online(data.driver_id)

        # Уведомляем клиента
        asyncio.create_task(manager.send_to_order(order_id, {
            "type": "order_completed",
            "order_id": order_id
        }))

        return {"message": "Order completed", "order_id": order_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{order_id}/cancel")
async def cancel_order(
        order_id: int,
        order_service: OrderService = Depends(),
        driver_service: DriverService = Depends()
):
    order = order_service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Проверяем, что заказ еще не принят и не завершен
    if order.status not in [OrderStatus.PENDING.value, OrderStatus.ACCEPTED.value]:
        raise HTTPException(status_code=400, detail="Order cannot be cancelled")

    try:
        # Если заказ уже принят, освобождаем водителя
        if order.status == OrderStatus.ACCEPTED.value and order.driver_id:
            driver_service.set_online(order.driver_id)

        # Отменяем заказ
        order = order_service.cancel_order(order_id)

        # Уведомляем всех участников через вебсокет
        asyncio.create_task(manager.send_to_order(order_id, {
            "type": "order_cancelled",
            "order_id": order_id,
            "reason": "Cancelled by client"
        }))

        # Уведомляем водителей (если заказ был в статусе PENDING)
        if order.status == OrderStatus.CANCELLED.value:
            asyncio.create_task(manager.broadcast_to_drivers({
                "type": "order_cancelled",
                "order_id": order_id,
                "reason": "Cancelled by client"
            }))

        return {"message": "Order cancelled", "order_id": order_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))