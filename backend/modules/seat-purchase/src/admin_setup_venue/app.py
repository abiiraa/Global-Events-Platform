"""Admin: seed venue sections and seats for an event."""

from __future__ import annotations

from typing import Any

from common.auth import is_admin_authorized
from common.constants import (
    EVENT_PREFIX,
    SECTION_PREFIX,
    SEAT_PREFIX,
    STATUS_AVAILABLE,
    VALID_TIERS,
)
from common.dynamodb import batch_write_items, put_section_availability
from common.logger import logger
from common.responses import bad_request, created, forbidden, internal_error
from common.utils import parse_body, utc_now_iso, validate_required_fields


@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    try:
        if not is_admin_authorized(event):
            return forbidden("Admin authorization required.")

        body = parse_body(event)
        error = validate_required_fields(body, ["eventId", "sections"])
        if error:
            return bad_request(error)

        event_id = body["eventId"]
        sections = body["sections"]

        if not isinstance(sections, list) or len(sections) == 0:
            return bad_request("sections must be a non-empty array.")

        now = utc_now_iso()
        total_seats_created = 0

        for section in sections:
            section_id = section.get("sectionId", "")
            tier = section.get("tier", "")
            price = int(section.get("price", 0))
            seats = section.get("seats", [])

            if not section_id or not tier or not seats:
                return bad_request(f"Each section requires sectionId, tier, and seats. Got: {section_id}")
            if tier not in VALID_TIERS:
                return bad_request(f"Invalid tier '{tier}'. Must be one of: {', '.join(sorted(VALID_TIERS))}")

            seat_items = []
            for seat_label in seats:
                seat_items.append({
                    "PK": f"{EVENT_PREFIX}{event_id}#{SECTION_PREFIX}{section_id}",
                    "SK": f"{SEAT_PREFIX}{seat_label}",
                    "entityType": "SEAT",
                    "eventId": event_id,
                    "sectionId": section_id,
                    "seatLabel": seat_label,
                    "tier": tier,
                    "price": price,
                    "status": STATUS_AVAILABLE,
                    "createdAt": now,
                    "updatedAt": now,
                    "GSI2PK": f"{EVENT_PREFIX}{event_id}",
                    "GSI2SK": f"STATUS#{STATUS_AVAILABLE}#{SECTION_PREFIX}{section_id}#{SEAT_PREFIX}{seat_label}",
                })

            batch_write_items(seat_items)

            availability_item = {
                "PK": f"{EVENT_PREFIX}{event_id}",
                "SK": f"{SECTION_PREFIX}{section_id}",
                "entityType": "SECTION_AVAILABILITY",
                "eventId": event_id,
                "sectionId": section_id,
                "tier": tier,
                "price": price,
                "totalSeats": len(seats),
                "availableSeats": len(seats),
                "soldSeats": 0,
                "createdAt": now,
            }
            put_section_availability(availability_item)
            total_seats_created += len(seats)

        return created({
            "eventId": event_id,
            "sectionsCreated": len(sections),
            "totalSeatsCreated": total_seats_created,
        })

    except Exception:
        logger.exception("Unexpected error in admin_setup_venue")
        return internal_error()
