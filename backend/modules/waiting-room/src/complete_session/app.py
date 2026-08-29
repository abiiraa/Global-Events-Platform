"""
Complete Session Lambda — transitions a user from ADMITTED to COMPLETED.

Endpoint: POST /queue/complete

Called after the fan finishes purchasing tickets. This closes their waiting-room
session and decrements the admittedUsers counter so new fans can be admitted.

EventBridge integration point: when Phase 2 (ticket purchase) is built, the
ticket purchase confirmation Lambda will call this endpoint (or publish a
FanAdmissionCompleted event that this Lambda subscribes to) rather than
requiring the frontend to call it directly.
"""

from __future__ import annotations

from typing import Any

from common.constants import (
    EVENT_PREFIX,
    QUEUE_PREFIX,
    QUEUE_REGISTRATION_PREFIX,
    STATUS_ADMITTED,
    STATUS_COMPLETED,
    USER_PREFIX,
)
from common.dynamodb import increment_stats, query_user_queue, update_item
from common.logger import logger
from common.responses import bad_request, conflict, internal_error, not_found, success
from common.utils import parse_body, utc_now_iso, validate_required_fields


@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """API Gateway proxy handler for POST /queue/complete."""
    try:
        body = parse_body(event)
        validation_error = validate_required_fields(body, ["eventId", "userId"])
        if validation_error:
            return bad_request(validation_error)

        event_id: str = body["eventId"]
        user_id: str = body["userId"]

        if len(event_id) > 64 or len(user_id) > 128:
            return bad_request("eventId or userId exceeds maximum allowed length.")

        logger.append_keys(eventId=event_id, userId=user_id)
        logger.info("Processing complete session request")

        item = query_user_queue(user_id, event_id)
        if not item:
            return not_found(f"No queue entry found for user '{user_id}' in event '{event_id}'.")

        current_status = item.get("status", "")
        if current_status != STATUS_ADMITTED:
            return conflict(f"Cannot complete — current status is '{current_status}'.")

        queue_position = item.get("queuePosition", "")
        pk = item.get("PK", f"{EVENT_PREFIX}{event_id}")
        sk = item.get("SK", f"{QUEUE_PREFIX}{queue_position}")
        now = utc_now_iso()

        result = update_item(
            pk=pk,
            sk=sk,
            update_expression="SET #status = :new_status, completedAt = :now, updatedAt = :now, GSI3SK = :gsi3sk",
            expression_values={
                ":new_status": STATUS_COMPLETED,
                ":now": now,
                ":current_status": STATUS_ADMITTED,
                ":gsi3sk": f"STATUS#{STATUS_COMPLETED}#{queue_position}",
            },
            expression_names={"#status": "status"},
            condition_expression="#status = :current_status",
        )

        if result is None:
            return conflict("Queue entry status has already changed.")

        update_item(
            pk=f"{USER_PREFIX}{user_id}",
            sk=f"{QUEUE_REGISTRATION_PREFIX}{event_id}",
            update_expression="SET #status = :new_status, updatedAt = :now",
            expression_values={":new_status": STATUS_COMPLETED, ":now": now},
            expression_names={"#status": "status"},
        )

        increment_stats(
            event_id,
            {"admittedUsers": -1, "completedUsers": 1},
            shard_seed=user_id,
        )

        logger.info("Session completed", extra={"queuePosition": queue_position})

        return success({"message": "Session completed."})

    except Exception:
        logger.exception("Unexpected error in complete_session")
        return internal_error()
