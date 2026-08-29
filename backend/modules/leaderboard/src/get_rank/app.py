"""Get exact rank and score for a participant."""

from __future__ import annotations

from typing import Any

from common.dynamodb import calculate_rank, get_participant_summary
from common.logger import logger
from common.responses import bad_request, internal_error, not_found, success
from common.utils import get_path_parameter


@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    try:
        lb_id = get_path_parameter(event, "leaderboardId")
        participant_id = get_path_parameter(event, "participantId")
        
        if not lb_id or not participant_id:
            return bad_request("Path parameters leaderboardId and participantId are required.")

        summary = get_participant_summary(participant_id, lb_id)
        if not summary:
            return not_found("Participant has no score on this leaderboard.")

        score = int(summary.get("score", 0))
        
        # Calculate exact rank
        rank = calculate_rank(lb_id, score)

        return success({
            "leaderboardId": lb_id,
            "participantId": participant_id,
            "participantName": summary.get("participantName", ""),
            "score": score,
            "rank": rank,
            "updatedAt": summary.get("updatedAt", ""),
        })

    except Exception:
        logger.exception("Unexpected error in get_rank")
        return internal_error()
