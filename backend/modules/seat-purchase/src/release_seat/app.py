"""Release a held seat back to AVAILABLE."""

from __future__ import annotations

from typing import Any

from common.dynamodb import get_hold, release_seat
from common.logger import logger
from common.responses import bad_request, internal_error, not_found, conflict, success
from common.utils import get_path_parameter, utc_now_iso


@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    try:
        hold_id = get_path_parameter(event, "holdId")
        if not hold_id:
            return bad_request("Path parameter holdId is required.")

        hold = get_hold(hold_id)
        if not hold:
            return not_found("Hold not found.")

        event_id = hold["eventId"]
        section_id = hold["sectionId"]
        seat_label = hold["seatLabel"]
        now_iso = utc_now_iso()

        released = release_seat(
            event_id=event_id,
            section_id=section_id,
            seat_label=seat_label,
            hold_id=hold_id,
            now_iso=now_iso,
        )

        if not released:
            return conflict("Seat is no longer held by this hold or has already been sold.")

        return success({
            "released": True,
            "holdId": hold_id,
            "seatLabel": seat_label,
            "sectionId": section_id,
        })

    except Exception:
        logger.exception("Unexpected error in release_seat")
        return internal_error()
