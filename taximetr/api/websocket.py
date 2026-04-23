from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
import json
import sys


def debug_print(*args, **kwargs):
    print(*args, **kwargs, file=sys.stderr, flush=True)


from taximetr.model.schemas import DriverUpdateLocation
from taximetr.service.driver_service import DriverService
from taximetr.service.order_service import OrderService
from taximetr.service.stop_points import StopPointsService
from taximetr.service.websocket_manager import manager

router = APIRouter(tags=["websocket"])


# Вебсокет для отслеживания конкретного заказа (водитель и клиент)
@router.websocket("/ws/order/{order_id}")
async def websocket_order(websocket: WebSocket, order_id: int, order_service: OrderService = Depends(),
                          driver_service: DriverService = Depends(),
                          stop_points_service: StopPointsService = Depends()):
    debug_print(f"📡 New WebSocket connection for order {order_id}")
    await websocket.accept()
    debug_print(f"✅ Connection accepted for order {order_id}")

    try:
        # Ждем идентификацию
        data = await websocket.receive_json()
        role = data.get("role")  # "driver" или "client"
        user_id = data.get("user_id")

        debug_print(f"📨 Received identification: role={role}, user_id={user_id} for order {order_id}")

        if role not in ["driver", "client"]:
            debug_print(f"❌ Invalid role: {role}")
            await websocket.close(code=1008, reason="Invalid role")
            return

        # Проверяем заказ
        order = order_service.get_order(order_id)
        if not order:
            debug_print(f"❌ Order {order_id} not found")
            await websocket.close(code=1008, reason="Order not found")
            return

        # Для водителя проверяем, что он назначен на этот заказ
        if role == "driver":
            # Проверяем, назначен ли водитель
            if order.driver_id is None:
                debug_print(f"❌ Order {order_id} has no driver assigned yet")
                await websocket.close(code=1008, reason="Driver not assigned to this order yet")
                return

            if order.driver_id != user_id:
                debug_print(f"❌ Driver {user_id} not assigned to order {order_id} (assigned driver: {order.driver_id})")
                await websocket.close(code=1008, reason="Driver not assigned to this order")
                return

            debug_print(f"✅ Driver {user_id} verified for order {order_id}")

        # Получаем информацию о водителе (если назначен)
        driver = None
        driver_phone = None
        driver_name = None
        if order.driver_id:
            driver = driver_service.get_driver(order.driver_id)
            if driver:
                driver_phone = driver.phone
                driver_name = driver.name

        # Подключаем к заказу
        await manager.connect_to_order(websocket, order_id, role)
        debug_print(f"✅ {role} (id={user_id}) connected to order {order_id}")

        # Отправляем подтверждение
        response_data = {
            "type": "connected",
            "order_id": order_id,
            "role": role,
            "status": order.status,
            "order": order.model_dump(mode='json'),
            "stop_points": [sp.model_dump(mode='json') for sp in stop_points_service.get_stop_points(order_id)]
        }

        if driver_phone:
            response_data["driver_phone"] = driver_phone
        if driver_name:
            response_data["driver_name"] = driver_name

        await websocket.send_json(response_data)
        debug_print(f"📤 Sent connected confirmation to {role} for order {order_id}")

        # Обработка сообщений
        while True:
            message = await websocket.receive_json()
            msg_type = message.get("type")
            debug_print(f"📨 Received from {role}: {msg_type}")

            if msg_type == "update_location" and role == "driver":
                # Водитель обновляет геолокацию
                lat = message.get("lat")
                lng = message.get("lng")
                location = DriverUpdateLocation(lat=lat, lng=lng)
                driver_service.update_location(user_id, location)
                debug_print(f"📍 Driver {user_id} location updated: {lat}, {lng}")

                # Отправляем клиенту
                await manager.send_to_role_in_order(order_id, "client", {
                    "type": "driver_location",
                    "lat": lat,
                    "lng": lng
                })
                debug_print(f"📤 Sent driver location to client for order {order_id}")

            elif msg_type == "status_change":
                # Изменение статуса заказа
                new_status = message.get("status")
                debug_print(f"🔄 Status change requested: {new_status} by {role}")

                if role == "driver" and new_status in ["delivering", "completed"]:
                    order_service.update_status(order_id, new_status)

                    # Обновляем данные заказа
                    updated_order = order_service.get_order(order_id)

                    # Отправляем всем участникам заказа
                    await manager.send_to_order(order_id, {
                        "type": "status_changed",
                        "status": new_status,
                        "order": updated_order.model_dump(mode='json'),
                        "driver_phone": driver_phone if driver_phone else None,
                        "driver_name": driver_name if driver_name else None,
                        "stop_points": [sp.model_dump(mode='json') for sp in
                                        stop_points_service.get_stop_points(order_id)]
                    })
                    debug_print(f"✅ Status changed to {new_status} for order {order_id}")

    except WebSocketDisconnect:
        debug_print(f"🔌 WebSocket disconnected for order {order_id}")
        manager.disconnect_from_order(websocket)
    except Exception as e:
        debug_print(f"❌ Unexpected error in websocket_order: {e}")
        import traceback
        debug_print(traceback.format_exc())
        try:
            await websocket.close(code=1011, reason=str(e))
        except:
            pass


# Вебсокет для broadcast водителям (получение новых заказов)
@router.websocket("/ws/driver/{driver_id}")
async def websocket_driver_broadcast(websocket: WebSocket, driver_id: int, driver_service: DriverService = Depends()):
    debug_print(f"🚗 Driver broadcast connection for driver {driver_id}")
    driver = driver_service.get_driver(driver_id)
    if not driver:
        debug_print(f"❌ Driver {driver_id} not found")
        await websocket.close(code=1008, reason="Driver not found")
        return

    await manager.connect_driver(websocket, driver_id, driver.settings_id)
    driver_service.set_online(driver_id)
    debug_print(f"✅ Driver {driver_id} connected for broadcast")

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            debug_print(f"📨 Driver {driver_id} message: {msg_type}")

            if msg_type == "update_location":
                lat = data.get("lat")
                lng = data.get("lng")
                location = DriverUpdateLocation(lat=lat, lng=lng)
                driver_service.update_location(driver_id, location)
                debug_print(f"📍 Driver {driver_id} location updated: {lat}, {lng}")

    except WebSocketDisconnect:
        debug_print(f"🔌 Driver {driver_id} broadcast disconnected")
        manager.disconnect_driver(driver_id)
        driver_service.set_offline(driver_id)


@router.websocket("/ws/client/{client_id}/{settings_id}")
async def websocket_client(
        websocket: WebSocket,
        client_id: int,
        settings_id: int
):
    debug_print(f"👤 Client broadcast connection for client {client_id}, settings {settings_id}")
    await manager.connect_client(websocket, client_id, settings_id)
    debug_print(f"✅ Client {client_id} connected for broadcast")

    try:
        while True:
            data = await websocket.receive_json()
            # Обработка сообщений от клиента, если нужно
            pass
    except WebSocketDisconnect:
        debug_print(f"🔌 Client {client_id} broadcast disconnected")
        manager.disconnect_client(client_id)