"""Admin: seat inventory summary by event."""

from __future__ import annotations

from typing import Any

from common.auth import is_admin_authorized
from common.dynamodb import get_section_availability
from common.logger import logger
from common.responses import bad_request, forbidden, internal_error, success
from common.utils import get_path_parameter


@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    try:
        if not is_admin_authorized(event):
            return forbidden("Admin authorization required.")

        event_id = get_path_parameter(event, "eventId")
        if not event_id:
            return bad_request("Path parameter eventId is required.")

        sections = get_section_availability(event_id)

        result = []
        total_seats = 0
        total_available = 0
        total_sold = 0

        for s in sections:
            available = int(s.get("availableSeats", 0))
            sold = int(s.get("soldSeats", 0))
            total = int(s.get("totalSeats", 0))
            total_seats += total
            total_available += available
            total_sold += sold
            result.append({
                "sectionId": s.get("sectionId", ""),
                "tier": s.get("tier", ""),
                "price": int(s.get("price", 0)),
                "totalSeats": total,
                "availableSeats": available,
                "soldSeats": sold,
                "heldSeats": total - available - sold,
            })

        return success({
            "eventId": event_id,
            "sections": result,
            "summary": {
                "totalSeats": total_seats,
                "availableSeats": total_available,
                "soldSeats": total_sold,
                "heldSeats": total_seats - total_available - total_sold,
            },
        })

    except Exception:
        logger.exception("Unexpected error in admin_inventory")
        return internal_error()
