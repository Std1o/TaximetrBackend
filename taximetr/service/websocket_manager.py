from fastapi import WebSocket
from typing import Dict, Any, List
import sys


def debug_print(*args, **kwargs):
    """Принудительный вывод в stderr с немедленным сбросом буфера"""
    print(*args, **kwargs, file=sys.stderr, flush=True)


class ConnectionManager:
    def __init__(self):
        debug_print("🔧 ConnectionManager.__init__ вызван")
        # Храним соединения по заказам
        self.order_connections: Dict[int, Dict[str, Any]] = {}  # {order_id: {"driver": ws, "client": ws}}
        # Храним соединения водителей для broadcast
        self.driver_connections: Dict[int, Any] = {}  # {driver_id: websocket}
        self.client_connections: Dict[int, Any] = {}
        # НОВОЕ: Храним соединения для просмотра очереди
        self.queue_connections: Dict[int, List[WebSocket]] = {}  # {settings_id: [websocket1, websocket2]}

    # Методы для работы с заказами
    async def connect_to_order(self, websocket: WebSocket, order_id: int, role: str):
        debug_print(f"🔌 connect_to_order: order_id={order_id}, role={role}")
        debug_print(f"Current order_connections before: {list(self.order_connections.keys())}")

        if order_id not in self.order_connections:
            self.order_connections[order_id] = {}
            debug_print(f"Created new entry for order_id={order_id}")

        self.order_connections[order_id][role] = {
            "websocket": websocket,
            "role": role
        }

        debug_print(f"Roles for order_id={order_id}: {list(self.order_connections[order_id].keys())}")
        debug_print(f"Current order_connections after: {self.order_connections}")

    def disconnect_from_order(self, websocket: WebSocket):
        """Отключение от заказа"""
        debug_print(f"🔌 disconnect_from_order called")
        for order_id, connections in list(self.order_connections.items()):
            for role, conn in list(connections.items()):
                if conn["websocket"] == websocket:
                    debug_print(f"Removed {role} from order {order_id}")
                    del self.order_connections[order_id][role]
                    if not self.order_connections[order_id]:
                        del self.order_connections[order_id]
                        debug_print(f"Removed empty order {order_id}")
                    return

    async def send_to_order(self, order_id: int, data: dict):
        debug_print(f"📤 send_to_order: order_id={order_id}, type={data.get('type')}")
        debug_print(f"order_connections keys: {list(self.order_connections.keys())}")

        if order_id in self.order_connections:
            roles = list(self.order_connections[order_id].keys())
            debug_print(f"Roles for order_id={order_id}: {roles}")

            for role, conn in self.order_connections[order_id].items():
                try:
                    await conn["websocket"].send_json(data)
                    debug_print(f"✅ Sent to {role}")
                except Exception as e:
                    debug_print(f"❌ Error sending to {role}: {e}")
        else:
            debug_print(f"❌ order_id {order_id} NOT FOUND in order_connections")

    async def send_to_role_in_order(self, order_id: int, role: str, data: dict):
        """Отправить сообщение конкретному участнику заказа (водитель или клиент)"""
        debug_print(f"📤 send_to_role_in_order: order_id={order_id}, role={role}")
        if order_id in self.order_connections and role in self.order_connections[order_id]:
            try:
                await self.order_connections[order_id][role]["websocket"].send_json(data)
                debug_print(f"✅ Sent to {role} in order {order_id}")
            except Exception as e:
                debug_print(f"❌ Error sending to {role} in order {order_id}: {e}")
        else:
            debug_print(f"❌ order_id {order_id} or role {role} NOT FOUND")

    # Методы для работы с водителями (broadcast)
    async def connect_driver(self, websocket: WebSocket, driver_id: int, settings_id: int):
        debug_print(f"🚗 connect_driver: driver_id={driver_id}, settings_id={settings_id}")
        await websocket.accept()
        self.driver_connections[driver_id] = {
            "websocket": websocket,
            "settings_id": settings_id
        }
        debug_print(f"Driver {driver_id} connected. Total drivers: {len(self.driver_connections)}")

    def disconnect_driver(self, driver_id: int):
        """Отключение водителя от broadcast"""
        debug_print(f"🚗 disconnect_driver: driver_id={driver_id}")
        if driver_id in self.driver_connections:
            del self.driver_connections[driver_id]
            debug_print(f"Driver {driver_id} disconnected. Total drivers: {len(self.driver_connections)}")

    async def send_to_driver(self, driver_id: int, data: dict, factor: float = None):
        """Отправить сообщение конкретному водителю"""
        debug_print(f"📤 send_to_driver: driver_id={driver_id}, factor={factor}")
        if driver_id in self.driver_connections:
            try:
                if factor is not None:
                    data["factor"] = factor
                await self.driver_connections[driver_id]["websocket"].send_json(data)
                debug_print(f"✅ Sent to driver {driver_id}")
            except Exception as e:
                debug_print(f"❌ Error sending to driver {driver_id}: {e}")
        else:
            debug_print(f"❌ Driver {driver_id} NOT FOUND")

    async def broadcast_to_drivers(self, data: dict, settings_id: int, factor: float = None):
        debug_print(f"📢 broadcast_to_drivers: settings_id={settings_id}, factor={factor}")
        count = 0
        for driver_id, conn in self.driver_connections.items():
            if conn["settings_id"] == settings_id:
                try:
                    msg = data.copy()
                    if factor is not None:
                        msg["factor"] = factor
                    await conn["websocket"].send_json(msg)
                    count += 1
                except Exception as e:
                    debug_print(f"❌ Error broadcasting to driver {driver_id}: {e}")
        debug_print(f"✅ Broadcast sent to {count} drivers")

    async def connect_client(self, websocket: WebSocket, client_id: int, settings_id: int):
        """Подключение клиента для broadcast"""
        debug_print(f"👤 connect_client: client_id={client_id}, settings_id={settings_id}")
        await websocket.accept()
        self.client_connections[client_id] = {
            "websocket": websocket,
            "settings_id": settings_id
        }
        debug_print(f"Client {client_id} connected. Total clients: {len(self.client_connections)}")

    def disconnect_client(self, client_id: int):
        debug_print(f"👤 disconnect_client: client_id={client_id}")
        if client_id in self.client_connections:
            del self.client_connections[client_id]
            debug_print(f"Client {client_id} disconnected. Total clients: {len(self.client_connections)}")

    async def broadcast_to_clients(self, data: dict, settings_id: int):
        """Отправить сообщение всем клиентам региона"""
        debug_print(f"📢 broadcast_to_clients: settings_id={settings_id}")
        count = 0
        for client_id, conn in self.client_connections.items():
            if conn["settings_id"] == settings_id:
                try:
                    await conn["websocket"].send_json(data)
                    count += 1
                except Exception as e:
                    debug_print(f"❌ Error broadcasting to client {client_id}: {e}")
        debug_print(f"✅ Broadcast sent to {count} clients")

    # НОВЫЕ МЕТОДЫ ДЛЯ РАБОТЫ С ОЧЕРЕДЬЮ
    async def connect_queue(self, websocket: WebSocket, settings_id: int):
        """Подключение к просмотру очереди водителей"""
        debug_print(f"📊 connect_queue: settings_id={settings_id}")
        await websocket.accept()

        if settings_id not in self.queue_connections:
            self.queue_connections[settings_id] = []

        self.queue_connections[settings_id].append(websocket)
        debug_print(f"Queue connections for settings {settings_id}: {len(self.queue_connections[settings_id])}")

    def disconnect_queue(self, websocket: WebSocket):
        """Отключение от просмотра очереди"""
        debug_print(f"📊 disconnect_queue called")
        for settings_id, connections in list(self.queue_connections.items()):
            if websocket in connections:
                connections.remove(websocket)
                debug_print(f"Removed queue connection from settings {settings_id}")
                if not connections:
                    del self.queue_connections[settings_id]
                return

    async def broadcast_queue_update(self, settings_id: int, data: dict):
        """Отправить обновление очереди всем подключенным клиентам"""
        debug_print(f"📊 broadcast_queue_update: settings_id={settings_id}, type={data.get('type')}")

        if settings_id not in self.queue_connections:
            debug_print(f"No queue connections for settings {settings_id}")
            return

        for websocket in self.queue_connections[settings_id][:]:
            try:
                await websocket.send_json(data)
                debug_print(f"✅ Queue update sent")
            except Exception as e:
                debug_print(f"❌ Error sending queue update: {e}")
                self.queue_connections[settings_id].remove(websocket)

        if settings_id in self.queue_connections and not self.queue_connections[settings_id]:
            del self.queue_connections[settings_id]


debug_print("🚀 Creating ConnectionManager instance...")
manager = ConnectionManager()
debug_print("✅ ConnectionManager instance created")