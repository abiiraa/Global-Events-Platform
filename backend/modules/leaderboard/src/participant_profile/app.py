"""Get all leaderboards and scores for a specific participant."""

from __future__ import annotations

from typing import Any

from common.dynamodb import get_participant_profile, query_participant_leaderboards
from common.logger import logger
from common.responses import bad_request, internal_error, not_found, success
from common.utils import get_path_parameter


@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    try:
        participant_id = get_path_parameter(event, "participantId")
        if not participant_id:
            return bad_request("Path parameter participantId is required.")

        profile = get_participant_profile(participant_id)
        if not profile:
            return not_found("Participant not found.")

        # Get all leaderboards (GSI1)
        boards = query_participant_leaderboards(participant_id)

        formatted_boards = []
        for b in boards:
            formatted_boards.append({
                "leaderboardId": b.get("leaderboardId", ""),
                "score": int(b.get("score", 0)),
                "updatedAt": b.get("updatedAt", ""),
            })

        return success({
            "participantId": participant_id,
            "participantName": profile.get("participantName", ""),
            "leaderboards": formatted_boards,
            "totalLeaderboards": len(formatted_boards),
        })

    except Exception:
        logger.exception("Unexpected error in participant_profile")
        return internal_error()
