"""Place a conditional hold on a seat."""

from __future__ import annotations

from typing import Any

from common.constants import (
    HOLD_PREFIX,
    METADATA,
    STATUS_HELD,
)
from common.dynamodb import get_session, hold_seat, put_hold
from common.logger import logger
from common.responses import bad_request, conflict, gone, internal_error, success, unauthorized
from common.utils import (
    epoch_minutes_from_now,
    generate_id,
    get_hold_ttl_minutes,
    parse_body,
    utc_now_epoch,
    utc_now_iso,
    validate_required_fields,
)


@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    try:
        body = parse_body(event)
        error = validate_required_fields(body, ["sessionId", "eventId", "sectionId", "seatLabel"])
        if error:
            return bad_request(error)

        session_id = body["sessionId"]
        event_id = body["eventId"]
        section_id = body["sectionId"]
        seat_label = body["seatLabel"]

        session = get_session(session_id)
        if not session:
            return unauthorized("Invalid session.")
        if session.get("status") != "ACTIVE":
            return gone("Session is no longer active.")
        if session.get("eventId") != event_id:
            return bad_request("Session does not match the requested event.")

        fan_id = session["fanId"]
        hold_id = generate_id()
        hold_ttl = get_hold_ttl_minutes()
        hold_expires_at = epoch_minutes_from_now(hold_ttl)
        now_iso = utc_now_iso()
        now_epoch = utc_now_epoch()

        held = hold_seat(
            event_id=event_id,
            section_id=section_id,
            seat_label=seat_label,
            hold_id=hold_id,
            fan_id=fan_id,
            session_id=session_id,
            hold_expires_at=hold_expires_at,
            now_iso=now_iso,
            now_epoch=now_epoch,
        )

        if not held:
            return conflict("Seat is not available. It may be held or sold.")

        hold_item = {
            "PK": f"{HOLD_PREFIX}{hold_id}",
            "SK": METADATA,
            "holdId": hold_id,
            "eventId": event_id,
            "sectionId": section_id,
            "seatLabel": seat_label,
            "fanId": fan_id,
            "sessionId": session_id,
            "status": STATUS_HELD,
            "holdExpiresAt": hold_expires_at,
            "createdAt": now_iso,
            "ttl": hold_expires_at,
        }
        put_hold(hold_item)

        return success({
            "holdId": hold_id,
            "eventId": event_id,
            "sectionId": section_id,
            "seatLabel": seat_label,
            "holdExpiresAt": hold_expires_at,
            "holdTTLMinutes": hold_ttl,
        })

    except Exception:
        logger.exception("Unexpected error in hold_seat")
        return internal_error()
