"""Place a concession order from a fan's seat."""

from __future__ import annotations

from typing import Any

from common.constants import (
    EVENT_PREFIX,
    FAN_PREFIX,
    METADATA,
    ORDER_PREFIX,
    STAND_PREFIX,
    QUEUE_SUFFIX,
    STATUS_PENDING,
    VIP_PRIORITY,
    REGULAR_PRIORITY,
)
from common.dynamodb import (
    decrement_inventory,
    find_closest_stand_with_inventory,
    put_order,
    put_stand_queue_entry,
    put_fan_order_entry,
    query_stands_for_event,
    restore_inventory,
)
from common.logger import logger
from common.responses import bad_request, conflict, created, internal_error, not_found
from common.utils import (
    epoch_hours_from_now,
    generate_order_id,
    get_order_ttl_hours,
    parse_body,
    utc_now_iso,
    validate_required_fields,
)


@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    try:
        body = parse_body(event)
        error = validate_required_fields(body, ["eventId", "fanId", "section", "items"])
        if error:
            return bad_request(error)

        event_id = body["eventId"]
        fan_id = body["fanId"]
        fan_section = body["section"]
        items = body["items"]
        is_vip = body.get("isVip", False)

        if not isinstance(items, list) or len(items) == 0:
            return bad_request("items must be a non-empty array of {itemId, name, quantity}.")

        # Validate each item
        for item in items:
            if not item.get("itemId") or not item.get("name"):
                return bad_request("Each item requires itemId and name.")
            item["quantity"] = int(item.get("quantity", 1))

        # Find the closest stand with sufficient inventory
        stands = query_stands_for_event(event_id)
        if not stands:
            return not_found("No concession stands found for this event.")

        stand = find_closest_stand_with_inventory(stands, fan_section, items)
        if not stand:
            return conflict("No stand has sufficient inventory for all requested items.")

        stand_id = stand["standId"]

        # Atomically decrement inventory for each item
        decremented_items: list[dict[str, Any]] = []
        for item in items:
            ok = decrement_inventory(stand_id, item["itemId"], item["quantity"])
            if not ok:
                # Rollback previously decremented items
                for d in decremented_items:
                    restore_inventory(stand_id, d["itemId"], d["quantity"])
                return conflict(
                    f"Insufficient inventory for item '{item['name']}' at stand {stand_id}."
                )
            decremented_items.append(item)

        # Create the order
        order_id = generate_order_id()
        now = utc_now_iso()
        total_price = sum(
            int(item.get("price", 0)) * item["quantity"] for item in items
        )
        ttl = epoch_hours_from_now(get_order_ttl_hours())
        priority = VIP_PRIORITY if is_vip else REGULAR_PRIORITY

        order_item = {
            "PK": f"{ORDER_PREFIX}{order_id}",
            "SK": METADATA,
            "entityType": "ORDER",
            "orderId": order_id,
            "eventId": event_id,
            "fanId": fan_id,
            "section": fan_section,
            "standId": stand_id,
            "standName": stand.get("standName", ""),
            "items": items,
            "totalPrice": total_price,
            "status": STATUS_PENDING,
            "isVip": is_vip,
            "orderTime": now,
            "createdAt": now,
            "updatedAt": now,
            "ttl": ttl,
            # GSI3 — event-level analytics
            "GSI3PK": f"{EVENT_PREFIX}{event_id}",
            "GSI3SK": f"{STAND_PREFIX}{stand_id}#{ORDER_PREFIX}{now}#{order_id}",
        }
        put_order(order_item)

        # Add to stand queue (FIFO sorted by priority + order time)
        queue_sk = f"{ORDER_PREFIX}{priority}{now}#{order_id}"
        queue_entry = {
            "PK": f"{STAND_PREFIX}{stand_id}{QUEUE_SUFFIX}",
            "SK": queue_sk,
            "entityType": "QUEUE_ENTRY",
            "orderId": order_id,
            "eventId": event_id,
            "fanId": fan_id,
            "section": fan_section,
            "items": items,
            "totalPrice": total_price,
            "status": STATUS_PENDING,
            "isVip": is_vip,
            "orderTime": now,
            "standId": stand_id,
            # GSI1 — stand operator queue by status
            "GSI1PK": f"{EVENT_PREFIX}{event_id}#{STAND_PREFIX}{stand_id}#STATUS#{STATUS_PENDING}",
            "GSI1SK": f"{priority}{now}#{order_id}",
        }
        put_stand_queue_entry(queue_entry)

        # Add fan order pointer
        fan_entry = {
            "PK": f"{FAN_PREFIX}{fan_id}#ORDERS",
            "SK": f"{ORDER_PREFIX}{now}#{order_id}",
            "entityType": "FAN_ORDER",
            "orderId": order_id,
            "eventId": event_id,
            "standId": stand_id,
            "standName": stand.get("standName", ""),
            "totalPrice": total_price,
            "status": STATUS_PENDING,
            "orderTime": now,
            # GSI2 — fan order lookup by event
            "GSI2PK": f"{EVENT_PREFIX}{event_id}#{FAN_PREFIX}{fan_id}",
            "GSI2SK": f"{ORDER_PREFIX}{now}",
        }
        put_fan_order_entry(fan_entry)

        return created({
            "orderId": order_id,
            "standId": stand_id,
            "standName": stand.get("standName", ""),
            "status": STATUS_PENDING,
            "totalPrice": total_price,
            "items": items,
            "orderTime": now,
            "isVip": is_vip,
        })

    except Exception:
        logger.exception("Unexpected error in place_order")
        return internal_error()
