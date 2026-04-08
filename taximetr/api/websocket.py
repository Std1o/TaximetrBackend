from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
import json

from taximetr.model.schemas import DriverUpdateLocation
from taximetr.service.driver_service import DriverService
from taximetr.service.order_service import OrderService
from taximetr.service.websocket_manager import manager

router = APIRouter(tags=["websocket"])


# Вебсокет для отслеживания конкретного заказа (водитель и клиент)
@router.websocket("/ws/order/{order_id}")
async def websocket_order(websocket: WebSocket, order_id: int, order_service: OrderService = Depends(),
                          driver_service: DriverService = Depends()):
    await websocket.accept()

    try:
        # Ждем идентификацию
        data = await websocket.receive_json()
        role = data.get("role")  # "driver" или "client"
        user_id = data.get("user_id")

        if role not in ["driver", "client"]:
            await websocket.close(code=1008, reason="Invalid role")
            return

        # Проверяем заказ
        order = order_service.get_order(order_id)
        driver = driver_service.get_driver(order.driver_id)
        if not order:
            await websocket.close(code=1008, reason="Order not found")
            return

        # Для водителя проверяем, что он назначен на этот заказ
        if role == "driver":
            if order.driver_id != user_id:
                await websocket.close(code=1008, reason="Driver not assigned to this order")
                return

        # Подключаем к заказу
        await manager.connect_to_order(websocket, order_id, role)

        # Отправляем подтверждение
        await websocket.send_json({
            "type": "connected",
            "order_id": order_id,
            "role": role,
            "status": order.status,
            "order": order.model_dump(mode='json'),
            "driver_phone": driver.phone if driver else None,
            "driver_name": driver.name if driver else None
        })

        # Обработка сообщений
        while True:
            message = await websocket.receive_json()
            msg_type = message.get("type")

            if msg_type == "update_location" and role == "driver":
                # Водитель обновляет геолокацию
                lat = message.get("lat")
                lng = message.get("lng")
                location = DriverUpdateLocation(lat=lat, lng=lng)
                driver_service.update_location(user_id, location)

                # Отправляем клиенту
                await manager.send_to_role_in_order(order_id, "client", {
                    "type": "driver_location",
                    "lat": lat,
                    "lng": lng
                })

            elif msg_type == "status_change":
                # Изменение статуса заказа
                new_status = message.get("status")
                if role == "driver" and new_status in ["delivering", "completed"]:
                    order_service.update_status(order_id, new_status)
                    await manager.send_to_order(order_id, {
                        "type": "status_changed",
                        "status": new_status,
                        "order": order.model_dump(mode='json'),
                        "driver_phone": driver.phone if driver else None,
                        "driver_name": driver.name if driver else None
                    })

    except WebSocketDisconnect:
        manager.disconnect_from_order(websocket)


# Вебсокет для broadcast водителям (получение новых заказов)
@router.websocket("/ws/driver/{driver_id}")
async def websocket_driver_broadcast(websocket: WebSocket, driver_id: int, driver_service: DriverService = Depends()):
    driver = driver_service.get_driver(driver_id)
    await manager.connect_driver(websocket, driver_id, driver.settings_id)
    driver_service.set_online(driver_id)

    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "update_location":
                lat = data.get("lat")
                lng = data.get("lng")
                location = DriverUpdateLocation(lat=lat, lng=lng)
                driver_service.update_location(driver_id, location)

    except WebSocketDisconnect:
        manager.disconnect_driver(driver_id)
        driver_service.set_offline(driver_id)


@router.websocket("/ws/client/{client_id}/{settings_id}")
async def websocket_client(
        websocket: WebSocket,
        client_id: int,
        settings_id: int
):
    await manager.connect_client(websocket, client_id, settings_id)

    try:
        while True:
            data = await websocket.receive_json()
            # Обработка сообщений от клиента, если нужно
            pass
    except WebSocketDisconnect:
        manager.disconnect_client(client_id)