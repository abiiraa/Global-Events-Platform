"""Authentication helpers for the Leaderboard module."""

from __future__ import annotations

import os
from typing import Any


def is_admin_authorized(event: dict[str, Any]) -> bool:
    headers = event.get("headers") or {}
    headers_lower = {k.lower(): v for k, v in headers.items()}

    api_key = os.environ.get("ADMIN_API_KEY", "")
    if api_key and headers_lower.get("x-admin-api-key") == api_key:
        return True

    admin_email = os.environ.get("ADMIN_EMAIL", "")
    admin_password = os.environ.get("ADMIN_PASSWORD", "")
    if (
        admin_email
        and admin_password
        and headers_lower.get("x-admin-email") == admin_email
        and headers_lower.get("x-admin-password") == admin_password
    ):
        return True

    return False
