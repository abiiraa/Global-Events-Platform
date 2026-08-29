"""Get the queue of pending orders for a concession stand operator."""

from __future__ import annotations

from typing import Any

from common.constants import STATUS_PENDING
from common.dynamodb import query_stand_queue, query_stand_queue_by_status
from common.logger import logger
from common.responses import bad_request, internal_error, success
from common.utils import get_path_parameter, get_query_parameter


@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    try:
        stand_id = get_path_parameter(event, "standId")
        if not stand_id:
            return bad_request("Path parameter standId is required.")

        event_id = get_query_parameter(event, "eventId")
        status = get_query_parameter(event, "status", STATUS_PENDING)
        limit = int(get_query_parameter(event, "limit", "50"))

        if event_id and status:
            # Use GSI1 for status-filtered, time-sorted view
            orders = query_stand_queue_by_status(event_id, stand_id, status, limit)
        else:
            # Fall back to base table FIFO scan
            orders = query_stand_queue(stand_id, limit)

        return success({
            "standId": stand_id,
            "status": status,
            "orders": [
                {
                    "orderId": o.get("orderId", ""),
                    "fanId": o.get("fanId", ""),
                    "section": o.get("section", ""),
                    "items": o.get("items", []),
                    "totalPrice": int(o.get("totalPrice", 0)),
                    "status": o.get("status", ""),
                    "isVip": o.get("isVip", False),
                    "orderTime": o.get("orderTime", ""),
                }
                for o in orders
            ],
            "count": len(orders),
        })

    except Exception:
        logger.exception("Unexpected error in stand_queue")
        return internal_error()
