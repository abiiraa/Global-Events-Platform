"""Constants for the Concessions module."""

from __future__ import annotations

# Key prefixes
STAND_PREFIX: str = "STAND#"
ORDER_PREFIX: str = "ORDER#"
FAN_PREFIX: str = "FAN#"
EVENT_PREFIX: str = "EVENT#"
MENU_PREFIX: str = "MENU#"
QUEUE_SUFFIX: str = "#QUEUE"

# SK constants
METADATA: str = "METADATA"

# Order statuses
STATUS_PENDING: str = "PENDING"
STATUS_PREPARING: str = "PREPARING"
STATUS_READY: str = "READY"
STATUS_PICKED_UP: str = "PICKED_UP"
STATUS_CANCELLED: str = "CANCELLED"

VALID_STATUSES: set[str] = {
    STATUS_PENDING,
    STATUS_PREPARING,
    STATUS_READY,
    STATUS_PICKED_UP,
    STATUS_CANCELLED,
}

# Valid status transitions
VALID_TRANSITIONS: dict[str, set[str]] = {
    STATUS_PENDING: {STATUS_PREPARING, STATUS_CANCELLED},
    STATUS_PREPARING: {STATUS_READY},
    STATUS_READY: {STATUS_PICKED_UP},
}

# VIP priority prefix (sorts before regular "1#")
VIP_PRIORITY: str = "0#"
REGULAR_PRIORITY: str = "1#"

# GSI names
GSI1: str = "GSI1"
GSI2: str = "GSI2"
GSI3: str = "GSI3"

# Shard count for stand-level stats
STATS_SHARD_COUNT: int = 8

# Default order TTL (2 hours after creation)
DEFAULT_ORDER_TTL_HOURS: int = 2
