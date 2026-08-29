"""Constants for the Seat Purchase module."""

from __future__ import annotations

# Key prefixes
EVENT_PREFIX: str = "EVENT#"
SECTION_PREFIX: str = "SECTION#"
SEAT_PREFIX: str = "SEAT#"
HOLD_PREFIX: str = "HOLD#"
SESSION_PREFIX: str = "SESSION#"
TICKET_PREFIX: str = "TICKET#"
FAN_PREFIX: str = "FAN#"

# SK constants
METADATA: str = "METADATA"

# Seat statuses
STATUS_AVAILABLE: str = "AVAILABLE"
STATUS_HELD: str = "HELD"
STATUS_SOLD: str = "SOLD"

# Session statuses
SESSION_ACTIVE: str = "ACTIVE"
SESSION_COMPLETED: str = "COMPLETED"
SESSION_EXPIRED: str = "EXPIRED"

# Tier names
TIER_PREMIUM: str = "PREMIUM"
TIER_STANDARD: str = "STANDARD"
TIER_GENERAL: str = "GENERAL"

VALID_TIERS: set[str] = {TIER_PREMIUM, TIER_STANDARD, TIER_GENERAL}

# GSI names
GSI1: str = "GSI1"
GSI2: str = "GSI2"

# Hold TTL default (minutes)
DEFAULT_HOLD_TTL_MINUTES: int = 10
