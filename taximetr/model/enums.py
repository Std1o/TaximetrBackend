from enum import Enum

class OrderStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    DELIVERING = "delivering"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class DriverStatus(str, Enum):
    OFFLINE = "offline"
    ONLINE = "online"
    BUSY = "busy"

class DistributionAlgorithm(str, Enum):
    ROUND_ROBIN = "round_robin"
    NEAREST = "nearest"