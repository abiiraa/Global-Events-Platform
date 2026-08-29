"""Shared utilities for the Leaderboard module."""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from common.constants import MAX_SCORE_BASE, SHARD_COUNT


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_now_epoch() -> int:
    return int(time.time())


def generate_id() -> str:
    return uuid.uuid4().hex[:16]


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


def get_shard_id(participant_id: str) -> str:
    """Deterministically hash a participant to a shard."""
    return f"{hash(participant_id) % SHARD_COUNT:02x}"


def invert_score(score: int) -> str:
    """Invert score so DynamoDB ascending string sort results in descending numerical rank.
    
    DynamoDB sorts strings lexicographically. We want the highest score to sort first.
    We subtract the score from a large base and zero-pad it.
    Example with base 1000:
    Score 500 -> "0500"
    Score 900 -> "0100"
    "0100" sorts before "0500".
    """
    if score < 0:
        raise ValueError("Score cannot be negative")
    if score >= MAX_SCORE_BASE:
        raise ValueError(f"Score exceeds maximum allowed ({MAX_SCORE_BASE - 1})")
    
    inverted = MAX_SCORE_BASE - score
    return f"{inverted:010d}"
