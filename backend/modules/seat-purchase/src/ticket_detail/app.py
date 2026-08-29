"""Return full details for a single ticket."""

from __future__ import annotations

from typing import Any

from common.dynamodb import get_ticket
from common.logger import logger
from common.responses import bad_request, internal_error, not_found, success
from common.utils import get_path_parameter


@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    try:
        ticket_id = get_path_parameter(event, "ticketId")
        if not ticket_id:
            return bad_request("Path parameter ticketId is required.")

        ticket = get_ticket(ticket_id)
        if not ticket:
            return not_found("Ticket not found.")

        return success({
            "ticketId": ticket.get("ticketId", ""),
            "eventId": ticket.get("eventId", ""),
            "fanId": ticket.get("fanId", ""),
            "sectionId": ticket.get("sectionId", ""),
            "seatLabel": ticket.get("seatLabel", ""),
            "tier": ticket.get("tier", ""),
            "price": int(ticket.get("price", 0)),
            "status": ticket.get("status", ""),
            "purchasedAt": ticket.get("purchasedAt", ""),
            "holdId": ticket.get("holdId", ""),
            "sessionId": ticket.get("sessionId", ""),
        })

    except Exception:
        logger.exception("Unexpected error in ticket_detail")
        return internal_error()
