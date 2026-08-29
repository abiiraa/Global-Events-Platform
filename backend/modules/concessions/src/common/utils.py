"""Shared utilities for the Concessions module."""

from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_now_epoch() -> int:
    return int(time.time())


def epoch_hours_from_now(hours: int) -> int:
    return int(time.time()) + (hours * 3600)


def generate_id() -> str:
    return uuid.uuid4().hex[:16]


def generate_order_id() -> str:
    """Generate a short, unique order ID."""
    return uuid.uuid4().hex[:12].upper()


def parse_body(event: dict[str, Any]) -> dict[str, Any]:
    body = event.get("body")
    if body is None:
        return {}
    if isinstance(body, str):
        try:
            return json.loads(body)
        except (json.JSONDecodeError, TypeError):
            return {}
    return body if isinstance(body, dict) else {}


def get_path_parameter(event: dict[str, Any], name: str) -> Optional[str]:
    params = event.get("pathParameters") or {}
    return params.get(name)


def get_query_parameter(event: dict[str, Any], name: str, default: Optional[str] = None) -> Optional[str]:
    params = event.get("queryStringParameters") or {}
    return params.get(name, default)


def validate_required_fields(data: dict[str, Any], required: list[str]) -> Optional[str]:
    missing = [f for f in required if not data.get(f)]
    if missing:
        return f"Missing required fields: {', '.join(missing)}"
    return None


def get_order_ttl_hours() -> int:
    return int(os.environ.get("ORDER_TTL_HOURS", "2"))


def compute_shard_id(key: str, shard_count: int = 8) -> str:
    """Deterministic shard assignment based on hash of key."""
    return f"{hash(key) % shard_count:02x}"
