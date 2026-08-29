"""Shared utilities for the Seat Purchase module."""

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


def epoch_minutes_from_now(minutes: int) -> int:
    return int(time.time()) + (minutes * 60)


def generate_id() -> str:
    return uuid.uuid4().hex[:16]


def get_hold_ttl_minutes() -> int:
    return int(os.environ.get("HOLD_TTL_MINUTES", "10"))


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


def get_query_parameter(event: dict[str, Any], name: str) -> Optional[str]:
    params = event.get("queryStringParameters") or {}
    return params.get(name)


def validate_required_fields(data: dict[str, Any], required: list[str]) -> Optional[str]:
    missing = [f for f in required if not data.get(f)]
    if missing:
        return f"Missing required fields: {', '.join(missing)}"
    return None
