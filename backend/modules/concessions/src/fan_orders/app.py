"""Get all orders for a fan at an event."""

from __future__ import annotations

from typing import Any

from common.dynamodb import query_fan_orders
from common.logger import logger
from common.responses import bad_request, internal_error, success
from common.utils import get_path_parameter, get_query_parameter


@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    try:
        fan_id = get_path_parameter(event, "fanId")
        if not fan_id:
            return bad_request("Path parameter fanId is required.")

        event_id = get_query_parameter(event, "eventId")
        if not event_id:
            return bad_request("Query parameter eventId is required.")

        orders = query_fan_orders(event_id, fan_id)

        return success({
            "fanId": fan_id,
            "eventId": event_id,
            "orders": [
                {
                    "orderId": o.get("orderId", ""),
                    "standId": o.get("standId", ""),
                    "standName": o.get("standName", ""),
                    "totalPrice": int(o.get("totalPrice", 0)),
                    "status": o.get("status", ""),
                    "orderTime": o.get("orderTime", ""),
                }
                for o in orders
            ],
            "count": len(orders),
        })

    except Exception:
        logger.exception("Unexpected error in fan_orders")
        return internal_error()
