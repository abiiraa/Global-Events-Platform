"""Get the status of a concession order."""

from __future__ import annotations

from typing import Any

from common.dynamodb import get_order
from common.logger import logger
from common.responses import bad_request, internal_error, not_found, success
from common.utils import get_path_parameter


@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    try:
        order_id = get_path_parameter(event, "orderId")
        if not order_id:
            return bad_request("Path parameter orderId is required.")

        order = get_order(order_id)
        if not order:
            return not_found(f"Order {order_id} not found.")

        return success({
            "orderId": order.get("orderId", ""),
            "eventId": order.get("eventId", ""),
            "fanId": order.get("fanId", ""),
            "standId": order.get("standId", ""),
            "standName": order.get("standName", ""),
            "section": order.get("section", ""),
            "items": order.get("items", []),
            "totalPrice": int(order.get("totalPrice", 0)),
            "status": order.get("status", ""),
            "isVip": order.get("isVip", False),
            "orderTime": order.get("orderTime", ""),
            "updatedAt": order.get("updatedAt", ""),
        })

    except Exception:
        logger.exception("Unexpected error in order_status")
        return internal_error()
