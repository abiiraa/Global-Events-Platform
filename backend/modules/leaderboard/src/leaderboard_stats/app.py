"""Get stats for a leaderboard."""

from __future__ import annotations

from typing import Any

from common.dynamodb import get_leaderboard
from common.logger import logger
from common.responses import bad_request, internal_error, not_found, success
from common.utils import get_path_parameter


@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    try:
        lb_id = get_path_parameter(event, "leaderboardId")
        if not lb_id:
            return bad_request("Path parameter leaderboardId is required.")

        lb = get_leaderboard(lb_id)
        if not lb:
            return not_found(f"Leaderboard {lb_id} not found.")

        # In a real implementation, we might store aggregated stats on the leaderboard metadata item
        # updating them asynchronously via DynamoDB Streams.
        # For this challenge, we return basic info.

        return success({
            "leaderboardId": lb_id,
            "name": lb.get("name", ""),
            "createdAt": lb.get("createdAt", ""),
        })

    except Exception:
        logger.exception("Unexpected error in leaderboard_stats")
        return internal_error()
