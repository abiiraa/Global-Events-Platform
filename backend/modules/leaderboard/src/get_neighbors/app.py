"""Get neighboring records around a participant."""

from __future__ import annotations

from typing import Any

from common.dynamodb import get_participant_summary, query_neighbors
from common.logger import logger
from common.responses import bad_request, internal_error, not_found, success
from common.utils import get_path_parameter, get_query_parameter


@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    try:
        lb_id = get_path_parameter(event, "leaderboardId")
        participant_id = get_path_parameter(event, "participantId")
        
        if not lb_id or not participant_id:
            return bad_request("Path parameters leaderboardId and participantId are required.")

        limit = int(get_query_parameter(event, "limit", "3"))

        summary = get_participant_summary(participant_id, lb_id)
        if not summary:
            return not_found("Participant has no score on this leaderboard.")

        score = int(summary.get("score", 0))
        
        neighbors = query_neighbors(lb_id, participant_id, score, limit)

        formatted = []
        for item in neighbors:
            formatted.append({
                "participantId": item.get("participantId", ""),
                "participantName": item.get("participantName", ""),
                "score": int(item.get("score", 0)),
            })

        return success({
            "leaderboardId": lb_id,
            "participantId": participant_id,
            "score": score,
            "neighbors": formatted,
        })

    except Exception:
        logger.exception("Unexpected error in get_neighbors")
        return internal_error()
