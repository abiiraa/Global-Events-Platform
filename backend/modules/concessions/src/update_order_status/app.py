"""Update a concession order's status (state machine transitions)."""

from __future__ import annotations

from typing import Any

from common.auth import is_admin_authorized
from common.constants import (
    STATUS_CANCELLED,
    STATUS_PENDING,
    VALID_TRANSITIONS,
    REGULAR_PRIORITY,
    VIP_PRIORITY,
    ORDER_PREFIX,
    STAND_PREFIX,
    QUEUE_SUFFIX,
)
from common.dynamodb import (
    get_order,
    restore_inventory,
    update_order_status_conditional,
    update_stand_queue_entry_status,
)
from common.logger import logger
from common.responses import bad_request, conflict, forbidden, internal_error, not_found, success
from common.utils import get_path_parameter, parse_body, utc_now_iso


@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    try:
        if not is_admin_authorized(event):
            return forbidden("Admin authorization required.")

        order_id = get_path_parameter(event, "orderId")
        if not order_id:
            return bad_request("Path parameter orderId is required.")

        body = parse_body(event)
        new_status = body.get("status", "")
        if not new_status:
            return bad_request("Request body must include 'status'.")

        order = get_order(order_id)
        if not order:
            return not_found(f"Order {order_id} not found.")

        current_status = order.get("status", "")
        valid_next = VALID_TRANSITIONS.get(current_status, set())
        if new_status not in valid_next:
            return conflict(
                f"Cannot transition from {current_status} to {new_status}. "
                f"Valid transitions: {', '.join(sorted(valid_next)) if valid_next else 'none (terminal state)'}."
            )

        now = utc_now_iso()

        # If cancelling, restore inventory
        if new_status == STATUS_CANCELLED:
            items = order.get("items", [])
            stand_id = order.get("standId", "")
            for item in items:
                restore_inventory(stand_id, item["itemId"], int(item.get("quantity", 1)))

        updated = update_order_status_conditional(order_id, current_status, new_status, now)
        if not updated:
            return conflict(f"Order status has changed since read. Retry the operation.")

        # Update the stand queue entry's GSI1 keys so status-filtered queries reflect new status
        stand_id = order.get("standId", "")
        event_id = order.get("eventId", "")
        order_time = order.get("orderTime", "")
        is_vip = order.get("isVip", False)
        priority = VIP_PRIORITY if is_vip else REGULAR_PRIORITY
        queue_sk = f"{ORDER_PREFIX}{priority}{order_time}#{order_id}"

        try:
            update_stand_queue_entry_status(
                stand_id=stand_id,
                queue_sk=queue_sk,
                event_id=event_id,
                order_id=order_id,
                new_status=new_status,
                order_time=f"{priority}{order_time}",
                now_iso=now,
            )
        except Exception:
            logger.warning("Failed to update stand queue entry GSI1", exc_info=True)

        return success({
            "orderId": order_id,
            "previousStatus": current_status,
            "newStatus": new_status,
            "updatedAt": now,
        })

    except Exception:
        logger.exception("Unexpected error in update_order_status")
        return internal_error()
