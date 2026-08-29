"""Admin: seed concession stands with menu items and section coverage."""

from __future__ import annotations

from typing import Any

from common.auth import is_admin_authorized
from common.constants import (
    EVENT_PREFIX,
    MENU_PREFIX,
    METADATA,
    STAND_PREFIX,
    GSI3,
)
from common.dynamodb import batch_write_items, put_stand
from common.logger import logger
from common.responses import bad_request, created, forbidden, internal_error
from common.utils import generate_id, parse_body, utc_now_iso, validate_required_fields


@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    try:
        if not is_admin_authorized(event):
            return forbidden("Admin authorization required.")

        body = parse_body(event)
        error = validate_required_fields(body, ["eventId", "stands"])
        if error:
            return bad_request(error)

        event_id = body["eventId"]
        stands = body["stands"]

        if not isinstance(stands, list) or len(stands) == 0:
            return bad_request("stands must be a non-empty array.")

        now = utc_now_iso()
        total_menu_items = 0

        for stand_data in stands:
            stand_id = stand_data.get("standId", generate_id())
            stand_name = stand_data.get("standName", "")
            covered_sections = stand_data.get("coveredSections", [])
            section_distance = stand_data.get("sectionDistance", {})
            menu = stand_data.get("menu", [])

            if not stand_name:
                return bad_request("Each stand requires a standName.")
            if not covered_sections:
                return bad_request(f"Stand '{stand_name}' requires coveredSections.")

            # Create stand metadata
            stand_item = {
                "PK": f"{STAND_PREFIX}{stand_id}",
                "SK": METADATA,
                "entityType": "STAND",
                "standId": stand_id,
                "standName": stand_name,
                "eventId": event_id,
                "coveredSections": covered_sections,
                "sectionDistance": section_distance,
                "menuItemCount": len(menu),
                "createdAt": now,
                # GSI3 — event-level stand listing
                "GSI3PK": f"{EVENT_PREFIX}{event_id}",
                "GSI3SK": f"{STAND_PREFIX}{stand_id}",
            }
            put_stand(stand_item)

            # Create menu items
            menu_items = []
            for mi in menu:
                item_id = mi.get("itemId", generate_id())
                menu_items.append({
                    "PK": f"{STAND_PREFIX}{stand_id}",
                    "SK": f"{MENU_PREFIX}{item_id}",
                    "entityType": "MENU_ITEM",
                    "itemId": item_id,
                    "itemName": mi.get("itemName", ""),
                    "category": mi.get("category", "food"),
                    "price": int(mi.get("price", 0)),
                    "inventory": int(mi.get("inventory", 1000)),
                    "standId": stand_id,
                    "eventId": event_id,
                    "createdAt": now,
                })

            if menu_items:
                batch_write_items(menu_items)
            total_menu_items += len(menu_items)

        return created({
            "eventId": event_id,
            "standsCreated": len(stands),
            "totalMenuItems": total_menu_items,
        })

    except Exception:
        logger.exception("Unexpected error in admin_setup_stands")
        return internal_error()
