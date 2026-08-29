"""Submit or update a score on a leaderboard."""

from __future__ import annotations

from typing import Any

from common.dynamodb import get_leaderboard, get_participant_summary, submit_score_transaction
from common.logger import logger
from common.responses import bad_request, internal_error, not_found, success
from common.utils import parse_body, utc_now_iso, validate_required_fields


@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    try:
        body = parse_body(event)
        error = validate_required_fields(body, ["leaderboardId", "participantId", "participantName", "score"])
        if error:
            return bad_request(error)

        lb_id = body["leaderboardId"]
        participant_id = body["participantId"]
        participant_name = body["participantName"]
        score_data = body.get("scoreData", {})
        
        try:
            new_score = int(body["score"])
            if new_score < 0:
                return bad_request("Score cannot be negative.")
        except ValueError:
            return bad_request("Score must be an integer.")

        # Ensure leaderboard exists
        lb = get_leaderboard(lb_id)
        if not lb:
            return not_found(f"Leaderboard {lb_id} not found.")

        # Check if participant already has a score (to delete the old shard entry)
        summary = get_participant_summary(participant_id, lb_id)
        previous_score = None
        
        if summary:
            previous_score = int(summary.get("score", 0))
            # If the new score isn't better (assuming higher is better), we might not want to update.
            # For this challenge, we'll allow any update.
            if new_score <= previous_score:
                logger.info("New score is not higher than previous, updating anyway.")

        now = utc_now_iso()
        submit_score_transaction(
            lb_id=lb_id,
            participant_id=participant_id,
            new_score=new_score,
            now_iso=now,
            participant_name=participant_name,
            score_data=score_data,
            previous_score=previous_score,
        )

        return success({
            "leaderboardId": lb_id,
            "participantId": participant_id,
            "score": new_score,
            "previousScore": previous_score,
            "updatedAt": now,
        })

    except Exception:
        logger.exception("Unexpected error in submit_score")
        return internal_error()
