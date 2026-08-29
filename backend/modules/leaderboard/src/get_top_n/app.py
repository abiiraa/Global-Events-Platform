"""Get the Top N records from a leaderboard."""

from __future__ import annotations

from typing import Any

from common.dynamodb import get_leaderboard, query_top_n_scatter_gather
from common.logger import logger
from common.responses import bad_request, internal_error, not_found, success
from common.utils import get_path_parameter, get_query_parameter


@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    try:
        lb_id = get_path_parameter(event, "leaderboardId")
        if not lb_id:
            return bad_request("Path parameter leaderboardId is required.")

        limit_str = get_query_parameter(event, "limit", "10")
        try:
            limit = int(limit_str)
            if limit < 1 or limit > 100:
                return bad_request("Limit must be between 1 and 100.")
        except ValueError:
            return bad_request("Limit must be an integer.")

        # Ensure leaderboard exists
        lb = get_leaderboard(lb_id)
        if not lb:
            return not_found(f"Leaderboard {lb_id} not found.")

        items = query_top_n_scatter_gather(lb_id, limit)

        # Format output
        rankings = []
        for i, item in enumerate(items):
            rankings.append({
                "rank": i + 1,
                "participantId": item.get("participantId", ""),
                "participantName": item.get("participantName", ""),
                "score": int(item.get("score", 0)),
                "updatedAt": item.get("updatedAt", ""),
            })

        return success({
            "leaderboardId": lb_id,
            "leaderboardName": lb.get("name", ""),
            "limit": limit,
            "rankings": rankings,
        })

    except Exception:
        logger.exception("Unexpected error in get_top_n")
        return internal_error()
