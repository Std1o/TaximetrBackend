from fastapi import WebSocket
from typing import Dict, Any


class ConnectionManager:
    def __init__(self):
        # Храним соединения по заказам
        self.order_connections: Dict[int, Dict[str, Any]] = {}  # {order_id: {"driver": ws, "client": ws}}
        # Храним соединения водителей для broadcast
        self.driver_connections: Dict[int, Any] = {}  # {driver_id: websocket}
        self.client_connections: Dict[int, Any] = {}

    # Методы для работы с заказами
    async def connect_to_order(self, websocket: WebSocket, order_id: int, role: str):
        """Подключение к заказу (водитель или клиент)"""

        if order_id not in self.order_connections:
            self.order_connections[order_id] = {}

        self.order_connections[order_id][role] = {
            "websocket": websocket,
            "role": role
        }

    def disconnect_from_order(self, websocket: WebSocket):
        """Отключение от заказа"""
        for order_id, connections in list(self.order_connections.items()):
            for role, conn in list(connections.items()):
                if conn["websocket"] == websocket:
                    del self.order_connections[order_id][role]
                    if not self.order_connections[order_id]:
                        del self.order_connections[order_id]
                    return

    async def send_to_order(self, order_id: int, data: dict):
        """Отправить сообщение всем участникам заказа"""
        if order_id in self.order_connections:
            for role, conn in self.order_connections[order_id].items():
                try:
                    await conn["websocket"].send_json(data)
                except:
                    pass

    async def send_to_role_in_order(self, order_id: int, role: str, data: dict):
        """Отправить сообщение конкретному участнику заказа (водитель или клиент)"""
        if order_id in self.order_connections and role in self.order_connections[order_id]:
            try:
                await self.order_connections[order_id][role]["websocket"].send_json(data)
            except:
                pass

    # Методы для работы с водителями (broadcast)
    async def connect_driver(self, websocket: WebSocket, driver_id: int, settings_id: int):
        await websocket.accept()
        self.driver_connections[driver_id] = {
            "websocket": websocket,
            "settings_id": settings_id
        }

    def disconnect_driver(self, driver_id: int):
        """Отключение водителя от broadcast"""
        if driver_id in self.driver_connections:
            del self.driver_connections[driver_id]

    async def send_to_driver(self, driver_id: int, data: dict, factor: float = None):
        """Отправить сообщение конкретному водителю"""
        if driver_id in self.driver_connections:
            try:
                if factor is not None:
                    data["factor"] = factor
                await self.driver_connections[driver_id]["websocket"].send_json(data)
            except:
                pass

    async def broadcast_to_drivers(self, data: dict, settings_id: int, factor: float = None):
        for driver_id, conn in self.driver_connections.items():
            if conn["settings_id"] == settings_id:
                try:
                    msg = data.copy()
                    if factor is not None:
                        msg["factor"] = factor
                    await conn["websocket"].send_json(msg)
                except:
                    pass

    async def connect_client(self, websocket: WebSocket, client_id: int, settings_id: int):
        """Подключение клиента для broadcast"""
        await websocket.accept()
        self.client_connections[client_id] = {
            "websocket": websocket,
            "settings_id": settings_id
        }

    def disconnect_client(self, client_id: int):
        if client_id in self.client_connections:
            del self.client_connections[client_id]

    async def broadcast_to_clients(self, data: dict, settings_id: int):
        """Отправить сообщение всем клиентам региона"""
        for client_id, conn in self.client_connections.items():
            if conn["settings_id"] == settings_id:
                try:
                    await conn["websocket"].send_json(data)
                except:
                    pass


manager = ConnectionManager()