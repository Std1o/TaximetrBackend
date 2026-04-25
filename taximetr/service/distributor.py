import math
from typing import List, Optional
from sqlalchemy.orm import Session

from taximetr.database import get_session
from taximetr.model.enums import DistributionAlgorithm, OrderStatus
from taximetr.service.driver_service import DriverService
from taximetr.service.order_service import OrderService
from taximetr.service.settings_service import SettingsService
from taximetr.service.stop_points import StopPointsService
from taximetr.service.websocket_manager import manager
from taximetr.tables import Driver, Order
import asyncio


class OrderDistributor:
    def __init__(self):
        self.round_robin_index = {}
        self.rejected_orders = {}
        self.pending_orders = {}

    def calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        return math.sqrt((lat1 - lat2) ** 2 + (lng1 - lng2) ** 2)

    # НОВЫЙ МЕТОД
    def _broadcast_queue_update(self, settings_id: int):
        """Отправить обновление очереди всем подключенным клиентам"""
        import asyncio
        from taximetr.service.driver_service import DriverService

        async def broadcast():
            db = get_session()
            try:
                driver_service = DriverService(db)
                online_drivers = driver_service.get_online_drivers(settings_id)

                sorted_drivers = sorted(online_drivers, key=lambda d: d.id)
                driver_ids = [d.id for d in sorted_drivers]
                key = tuple(driver_ids)
                current_index = self.round_robin_index.get(key, 0)
                total = len(sorted_drivers)

                queue_data = []
                for i, driver in enumerate(sorted_drivers):
                    if total > 0:
                        position = (i - current_index) % total
                    else:
                        position = -1

                    queue_data.append({
                        "driver_id": driver.id,
                        "driver_name": driver.name,
                        "position": position,
                        "is_current": position == 0,
                    })

                await manager.broadcast_queue_update(settings_id, {
                    "type": "queue_updated",
                    "settings_id": settings_id,
                    "queue": queue_data,
                    "current_index": current_index,
                    "total_drivers": total,
                    "timestamp": __import__('datetime').datetime.now().isoformat()
                })
            finally:
                db.close()

        asyncio.create_task(broadcast())

    def get_next_driver_round_robin(self, online_drivers: List[Driver],
                                    rejected_drivers: List[int] = None) -> Optional[Driver]:
        if not online_drivers:
            return None

        # Фильтруем водителей, которые уже отказались
        if rejected_drivers:
            available_drivers = [d for d in online_drivers if d.id not in rejected_drivers]
            if not available_drivers:
                return None
        else:
            available_drivers = online_drivers

        # available_drivers уже отсортированы по id из сервиса
        driver_ids = [d.id for d in available_drivers]
        key = tuple(driver_ids)

        if key not in self.round_robin_index:
            self.round_robin_index[key] = 0

        index = self.round_robin_index[key]
        driver = available_drivers[index % len(available_drivers)]
        self.round_robin_index[key] = (index + 1) % len(available_drivers)

        # 👇 ДОБАВЛЕН ВЫЗОВ
        if available_drivers:
            self._broadcast_queue_update(available_drivers[0].settings_id)

        return driver

    def get_nearest_driver(self, order_lat: float, order_lng: float,
                           online_drivers: List[Driver],
                           rejected_drivers: List[int] = None) -> Optional[Driver]:
        if not online_drivers:
            return None

        # Фильтруем водителей, которые уже отказались
        if rejected_drivers:
            available_drivers = [d for d in online_drivers if d.id not in rejected_drivers]
            if not available_drivers:
                return None
        else:
            available_drivers = online_drivers

        return min(
            available_drivers,
            key=lambda d: self.calculate_distance(
                order_lat, order_lng, d.current_lat, d.current_lng
            )
        )

    async def redistribute_order(self, order: Order, order_service: OrderService, rejected_driver_id: int,
                                 stop_points_service: StopPointsService):
        # Добавляем водителя в список отказавшихся
        if order.id not in self.rejected_orders:
            self.rejected_orders[order.id] = []
        self.rejected_orders[order.id].append(rejected_driver_id)

        driver_service = DriverService(order_service.db)
        settings_service = SettingsService(order_service.db)

        online_drivers = driver_service.get_online_drivers(order.settings_id)
        rejected_drivers = self.rejected_orders.get(order.id, [])

        if not online_drivers:
            await self.cancel_order(order, order_service, stop_points_service, "Нет свободных водителей")
            return

        available_drivers = [d for d in online_drivers if d.id not in rejected_drivers]
        if not available_drivers:
            await self.cancel_order(order, order_service, stop_points_service, "Все водители отказались от заказа")
            return

        algorithm = settings_service.get_algorithm(order.settings_id)

        if algorithm == DistributionAlgorithm.ROUND_ROBIN:
            driver = self.get_next_driver_round_robin(online_drivers, rejected_drivers)
        else:
            driver = self.get_nearest_driver(
                order.pickup_lat, order.pickup_lng, online_drivers, rejected_drivers
            )

        if driver:
            await manager.send_to_driver(driver.id, {
                "type": "new_order",
                "order": {
                    "id": order.id,
                    "client_name": order.client_name,
                    "client_phone": order.client_phone,
                    "pickup_address": order.pickup_address,
                    "delivery_address": order.delivery_address,
                    "pickup_lat": order.pickup_lat,
                    "pickup_lng": order.pickup_lng,
                    "delivery_lat": order.delivery_lat,
                    "delivery_lng": order.delivery_lng
                },
                "algorithm": algorithm.value,
                "previous_driver_rejected": True
            })
            # 👇 ДОБАВЛЕН ВЫЗОВ
            self._broadcast_queue_update(order.settings_id)
        else:
            await self.cancel_order(order, order_service, stop_points_service, "Не удалось найти водителя")

    async def distribute_order(self, order: Order, db: Session):
        driver_service = DriverService(db)
        settings_service = SettingsService(db)
        order_service = OrderService(db)
        stop_points_service = StopPointsService(db)

        online_drivers = driver_service.get_online_drivers(order.settings_id)
        factor = settings_service.get_settings(order.settings_id).factor

        # ✅ Если нет водителей - запускаем таймаут на 10 секунд
        if not online_drivers:
            asyncio.create_task(self._cancel_after_timeout(order, db, 10))
            return

        algorithm = settings_service.get_algorithm(order.settings_id)

        if algorithm == DistributionAlgorithm.ROUND_ROBIN:
            driver = self.get_next_driver_round_robin(online_drivers)
        else:
            driver = self.get_nearest_driver(
                order.pickup_lat, order.pickup_lng, online_drivers
            )

        if driver:
            # Сохраняем информацию об ожидающем заказе
            self.pending_orders[order.id] = {
                "driver_id": driver.id,
                "time": asyncio.get_event_loop().time(),
                "resolved": False
            }

            await manager.send_to_driver(driver.id, {
                "type": "new_order",
                "order": {
                    "id": order.id,
                    "client_name": order.client_name,
                    "client_phone": order.client_phone,
                    "pickup_address": order.pickup_address,
                    "delivery_address": order.delivery_address,
                    "pickup_lat": order.pickup_lat,
                    "pickup_lng": order.pickup_lng,
                    "delivery_lat": order.delivery_lat,
                    "delivery_lng": order.delivery_lng
                },
                "algorithm": algorithm.value
            }, factor=factor)

            for d in online_drivers:
                if d.id != driver.id:
                    await manager.send_to_driver(d.id, {
                        "type": "order_taken",
                        "order_id": order.id,
                        "taken_by": driver.name
                    }, factor=factor)

            # 👇 ДОБАВЛЕН ВЫЗОВ
            self._broadcast_queue_update(order.settings_id)

            # Запускаем проверку таймаута
            asyncio.create_task(self._check_timeout(order.id, db, driver.id))
        else:
            # ✅ Если водитель не найден (хотя online_drivers не пуст)
            await self.cancel_order(order, order_service, stop_points_service, "Не удалось назначить водителя")

    async def _cancel_after_timeout(self, order: Order, db: Session, delay: int):
        await asyncio.sleep(delay)

        # Проверяем, не появился ли водитель за это время
        driver_service = DriverService(db)
        online_drivers = driver_service.get_online_drivers(order.settings_id)

        if not online_drivers:
            order_service = OrderService(db)
            stop_points_service = StopPointsService(db)
            await self.cancel_order(order, order_service, stop_points_service, "Нет свободных водителей")
        else:
            # Водитель появился - распределяем
            await self.distribute_order(order, db)

    async def _check_timeout(self, order_id: int, db: Session, driver_id: int):
        """Проверка таймаута через 10 секунд"""
        await asyncio.sleep(10)

        if order_id in self.pending_orders:
            pending = self.pending_orders[order_id]
            if not pending["resolved"] and pending["driver_id"] == driver_id:
                await manager.send_to_driver(driver_id, {
                    "type": "order_timeout",
                    "order_id": order_id,
                    "message": "Вы не ответили на заказ в течение 10 секунд, заказ передан другому водителю"
                })
                # Водитель не ответил
                order_service = OrderService(db)
                stop_points_service = StopPointsService(db)
                order = order_service.get_table_order(order_id)
                if order and order.status == OrderStatus.PENDING.value:
                    # 👇 ДОБАВЛЕН ВЫЗОВ
                    self._broadcast_queue_update(order.settings_id)
                    await self.redistribute_order(order, order_service, driver_id, stop_points_service)
                del self.pending_orders[order_id]

    def resolve_order(self, order_id: int, driver_id: int):
        """Водитель ответил (принял или отклонил)"""
        if order_id in self.pending_orders:
            self.pending_orders[order_id]["resolved"] = True
            del self.pending_orders[order_id]
            # 👇 ДОБАВЛЕН ВЫЗОВ (нужно получить settings_id)
            from taximetr.service.order_service import OrderService
            from taximetr.tables import SessionLocal
            db = SessionLocal()
            try:
                order_service = OrderService(db)
                order = order_service.get_table_order(order_id)
                if order:
                    self._broadcast_queue_update(order.settings_id)
            finally:
                db.close()

    async def cancel_order(self, order: Order,
                           order_service: OrderService,
                           stop_points_service: StopPointsService,
                           reason: str = "Все водители отказались от заказа", ):
        """Отмена заказа"""
        order_service.cancel_order(order.id)
        order = order_service.get_order(order.id)

        await manager.send_to_order(order.id, {
            "type": "order_cancelled",
            "order_id": order.id,
            "reason": reason,
            "status": order.status,
            "order": order.model_dump(mode='json'),
            "stop_points": [sp.model_dump(mode='json') for sp in stop_points_service.get_stop_points(order.id)]
        })

        if order.id in self.rejected_orders:
            del self.rejected_orders[order.id]

        # 👇 ДОБАВЛЕН ВЫЗОВ
        self._broadcast_queue_update(order.settings_id)


distributor = OrderDistributor()