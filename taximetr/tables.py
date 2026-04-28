from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from taximetr.model.enums import DriverStatus, OrderStatus, DistributionAlgorithm

Base = declarative_base()


class Settings(Base):
    __tablename__ = "settings"

    id = sa.Column(sa.Integer, primary_key=True)
    algorithm = sa.Column(sa.String, default=DistributionAlgorithm.ROUND_ROBIN.value)
    factor = sa.Column(sa.Double, default=1.0)
    region = sa.Column(sa.String, nullable=False)
    payment = sa.Column(sa.Integer, default=200)
    card = sa.Column(sa.String, nullable=False)

class User(Base):
    __tablename__ = 'users'
    id = sa.Column(sa.Integer, primary_key=True)
    phone = sa.Column(sa.Text, unique=True, nullable=False)
    username = sa.Column(sa.Text)
    password_hash = sa.Column(sa.Text)
    premium = sa.Column(sa.Date)
    settings_id = sa.Column(sa.Integer, sa.ForeignKey(Settings.id))


class Driver(Base):
    __tablename__ = "drivers"

    id = sa.Column(sa.Integer, primary_key=True, index=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"), nullable=False)
    name = sa.Column(sa.String, nullable=False)
    phone = sa.Column(sa.String, nullable=False)
    license_photo = sa.Column(sa.String, nullable=True)  # фото прав
    is_approved = sa.Column(sa.Boolean, default=False)  # одобрен ли водитель
    status = sa.Column(sa.String, default=DriverStatus.OFFLINE.value)
    current_lat = sa.Column(sa.Float, default=0.0)
    current_lng = sa.Column(sa.Float, default=0.0)
    current_order_id = sa.Column(sa.Integer, nullable=True)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    settings_id = sa.Column(sa.Integer, sa.ForeignKey(Settings.id))
    current_car_id = sa.Column(sa.Integer)

    # Связь с машинами
    cars = relationship("Car", backref="driver", cascade="all, delete-orphan")


class Car(Base):
    __tablename__ = "cars"

    id = sa.Column(sa.Integer, primary_key=True, index=True)
    driver_id = sa.Column(sa.Integer, sa.ForeignKey("drivers.id"), nullable=False)
    brand = sa.Column(sa.String, nullable=False)
    model = sa.Column(sa.String, nullable=False)
    color = sa.Column(sa.String, nullable=False)
    license_plate = sa.Column(sa.String, nullable=False, unique=True)
    is_approved = sa.Column(sa.Boolean, default=False)  # одобрена ли машина
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    approved_at = sa.Column(sa.DateTime, nullable=True)


class Order(Base):
    __tablename__ = "orders"

    id = sa.Column(sa.Integer, primary_key=True, index=True)
    client_name = sa.Column(sa.String, nullable=False)
    client_phone = sa.Column(sa.String, nullable=False)
    pickup_address = sa.Column(sa.String, nullable=False)
    delivery_address = sa.Column(sa.String, nullable=False)
    pickup_lat = sa.Column(sa.Float, nullable=False)
    pickup_lng = sa.Column(sa.Float, nullable=False)
    delivery_lat = sa.Column(sa.Float, nullable=False)
    delivery_lng = sa.Column(sa.Float, nullable=False)
    status = sa.Column(sa.String, default=OrderStatus.PENDING.value)
    driver_id = sa.Column(sa.Integer, nullable=True)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    accepted_at = sa.Column(sa.DateTime, nullable=True)
    completed_at = sa.Column(sa.DateTime, nullable=True)
    settings_id = sa.Column(sa.Integer, sa.ForeignKey(Settings.id))
    price = sa.Column(sa.Double, default=0.0)

class Tariff(Base):
    __tablename__ = "tariffs"

    id = sa.Column(sa.Integer, primary_key=True, index=True)
    name = sa.Column(sa.String, nullable=False)
    min_cost = sa.Column(sa.Double, default=0.0)
    min_km = sa.Column(sa.Double, default=0.0)
    min_minutes = sa.Column(sa.Double, default=0.0)
    price_per_km = sa.Column(sa.Double, default=0.0)
    price_per_min = sa.Column(sa.Double, default=0.0)
    waiting_price_per_min = sa.Column(sa.Double, default=5.0)
    free_waiting_minutes = sa.Column(sa.Double, default=2.0)
    min_speed_kmh = sa.Column(sa.Integer, default=0)
    double_tariff_speed = sa.Column(sa.Integer, default=100)
    country_price_per_km = sa.Column(sa.Double, default=5.0)
    country_price_per_min = sa.Column(sa.Double, default=5.0)
    is_active = sa.Column(sa.Boolean, default=True)
    distance_and_time = sa.Column(sa.Boolean, default=True)
    settings_id = sa.Column(sa.Integer, sa.ForeignKey(Settings.id))

class DriversTickets(Base):
    __tablename__ = 'drivers_tickets'

    user_id = sa.Column(sa.Integer, sa.ForeignKey(User.id), primary_key=True)
    username = sa.Column(sa.String, nullable=False)
    phone = sa.Column(sa.Text)
    image_url = sa.Column(sa.String)
    debt = sa.Column(sa.Double)

class Tickets(Base):
    __tablename__ = 'tickets'

    user_id = sa.Column(sa.Integer, sa.ForeignKey(User.id), primary_key=True)
    username = sa.Column(sa.String, nullable=False)
    phone = sa.Column(sa.Text)
    image_url = sa.Column(sa.String)

class Premium(Base):
    __tablename__ = 'premium'

    settings_id = sa.Column(sa.Integer, sa.ForeignKey(Settings.id), primary_key=True)
    sum = sa.Column(sa.Integer, nullable=False)
    card = sa.Column(sa.String, nullable=False)

class StopPoints(Base):
    __tablename__ = 'stop_points'
    id = sa.Column(sa.Integer, primary_key=True)
    order_id = sa.Column(sa.Integer, sa.ForeignKey(Order.id))
    address = sa.Column(sa.Text)
    was_stopped = sa.Column(sa.Boolean, default=False)