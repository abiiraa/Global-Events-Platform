"""Confirm purchase: TransactWriteItems (HELD -> SOLD + ticket creation)."""

from __future__ import annotations

from typing import Any

from common.constants import (
    FAN_PREFIX,
    METADATA,
    TICKET_PREFIX,
    STATUS_SOLD,
)
from common.dynamodb import execute_purchase_transaction, get_hold, get_session
from common.logger import logger
from common.responses import bad_request, conflict, gone, internal_error, success, unauthorized
from common.utils import generate_id, parse_body, utc_now_iso, validate_required_fields


@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    try:
        body = parse_body(event)
        error = validate_required_fields(body, ["sessionId", "holdId"])
        if error:
            return bad_request(error)

        session_id = body["sessionId"]
        hold_id = body["holdId"]

        session = get_session(session_id)
        if not session:
            return unauthorized("Invalid session.")
        if session.get("status") != "ACTIVE":
            return gone("Session is no longer active.")

        hold = get_hold(hold_id)
        if not hold:
            return bad_request("Hold not found.")
        if hold.get("sessionId") != session_id:
            return bad_request("Hold does not belong to this session.")

        fan_id = session["fanId"]
        event_id = session["eventId"]
        section_id = hold["sectionId"]
        seat_label = hold["seatLabel"]
        ticket_id = generate_id()
        now_iso = utc_now_iso()

        ticket_item = {
            "PK": f"{TICKET_PREFIX}{ticket_id}",
            "SK": METADATA,
            "ticketId": ticket_id,
            "eventId": event_id,
            "fanId": fan_id,
            "sectionId": section_id,
            "seatLabel": seat_label,
            "tier": hold.get("tier", ""),
            "price": hold.get("price", 0),
            "status": STATUS_SOLD,
            "purchasedAt": now_iso,
            "holdId": hold_id,
            "sessionId": session_id,
        }

        purchased = execute_purchase_transaction(
            event_id=event_id,
            section_id=section_id,
            seat_label=seat_label,
            hold_id=hold_id,
            session_id=session_id,
            fan_id=fan_id,
            ticket_id=ticket_id,
            ticket_item=ticket_item,
            now_iso=now_iso,
        )

        if not purchased:
            return conflict("Purchase failed. Seat may no longer be held by you.")

        return success({
            "ticketId": ticket_id,
            "eventId": event_id,
            "sectionId": section_id,
            "seatLabel": seat_label,
            "fanId": fan_id,
            "purchasedAt": now_iso,
        })

    except Exception:
        logger.exception("Unexpected error in purchase_seat")
        return internal_error()
