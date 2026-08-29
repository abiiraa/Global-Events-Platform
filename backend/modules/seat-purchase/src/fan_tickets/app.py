"""Return all tickets for a fan."""

from __future__ import annotations

from typing import Any

from common.dynamodb import query_fan_tickets
from common.logger import logger
from common.responses import bad_request, internal_error, success
from common.utils import get_path_parameter


@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    try:
        fan_id = get_path_parameter(event, "fanId")
        if not fan_id:
            return bad_request("Path parameter fanId is required.")

        items = query_fan_tickets(fan_id)

        tickets = [
            {
                "ticketId": item.get("ticketId", ""),
                "eventId": item.get("eventId", ""),
                "fanId": item.get("fanId", fan_id),
                "sectionId": item.get("sectionId", ""),
                "seatLabel": item.get("seatLabel", ""),
                "tier": item.get("tier", ""),
                "price": int(item.get("price", 0)),
                "purchasedAt": item.get("purchasedAt", ""),
            }
            for item in items
        ]

        return success({"fanId": fan_id, "tickets": tickets, "count": len(tickets)})

    except Exception:
        logger.exception("Unexpected error in fan_tickets")
        return internal_error()
