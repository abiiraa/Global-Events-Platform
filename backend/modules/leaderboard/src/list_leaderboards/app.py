"""List all available leaderboards."""

from __future__ import annotations

from typing import Any

from common.dynamodb import list_leaderboards
from common.logger import logger
from common.responses import internal_error, success


@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    try:
        boards = list_leaderboards()

        formatted = []
        for b in boards:
            formatted.append({
                "leaderboardId": b.get("leaderboardId", ""),
                "name": b.get("name", ""),
                "type": b.get("type", ""),
                "createdAt": b.get("createdAt", ""),
            })

        return success({
            "leaderboards": formatted,
            "count": len(formatted),
        })

    except Exception:
        logger.exception("Unexpected error in list_leaderboards")
        return internal_error()
