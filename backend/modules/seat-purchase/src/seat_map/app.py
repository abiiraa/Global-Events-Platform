"""Return seat availability for a section."""

from __future__ import annotations

from typing import Any

from common.constants import STATUS_AVAILABLE, STATUS_HELD, STATUS_SOLD
from common.dynamodb import query_seats_in_section
from common.logger import logger
from common.responses import bad_request, internal_error, success
from common.utils import get_path_parameter, utc_now_epoch


@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    try:
        event_id = get_path_parameter(event, "eventId")
        section_id = get_path_parameter(event, "sectionId")

        if not event_id or not section_id:
            return bad_request("Path parameters eventId and sectionId are required.")

        items = query_seats_in_section(event_id, section_id)
        now_epoch = utc_now_epoch()

        seats = []
        for item in items:
            status = item.get("status", STATUS_AVAILABLE)
            if status == STATUS_HELD and int(item.get("holdExpiresAt", 0)) < now_epoch:
                status = STATUS_AVAILABLE

            seats.append({
                "seatLabel": item.get("seatLabel", ""),
                "status": status,
                "tier": item.get("tier", ""),
                "price": int(item.get("price", 0)),
            })

        return success({
            "eventId": event_id,
            "sectionId": section_id,
            "seats": seats,
            "totalSeats": len(seats),
            "availableCount": sum(1 for s in seats if s["status"] == STATUS_AVAILABLE),
        })

    except Exception:
        logger.exception("Unexpected error in seat_map")
        return internal_error()
