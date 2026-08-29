"""Get throughput stats for a concession stand."""

from __future__ import annotations

from typing import Any

from common.constants import (
    STATUS_PENDING,
    STATUS_PREPARING,
    STATUS_READY,
    STATUS_PICKED_UP,
    STATUS_CANCELLED,
)
from common.dynamodb import query_stand_queue
from common.logger import logger
from common.responses import bad_request, internal_error, success
from common.utils import get_path_parameter


@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    try:
        stand_id = get_path_parameter(event, "standId")
        if not stand_id:
            return bad_request("Path parameter standId is required.")

        # Fetch all queue entries and aggregate by status
        entries = query_stand_queue(stand_id, limit=5000)

        stats = {
            STATUS_PENDING: 0,
            STATUS_PREPARING: 0,
            STATUS_READY: 0,
            STATUS_PICKED_UP: 0,
            STATUS_CANCELLED: 0,
        }
        total_revenue = 0
        vip_count = 0

        for entry in entries:
            status = entry.get("status", STATUS_PENDING)
            if status in stats:
                stats[status] += 1
            total_revenue += int(entry.get("totalPrice", 0))
            if entry.get("isVip"):
                vip_count += 1

        return success({
            "standId": stand_id,
            "totalOrders": len(entries),
            "pendingOrders": stats[STATUS_PENDING],
            "preparingOrders": stats[STATUS_PREPARING],
            "readyOrders": stats[STATUS_READY],
            "completedOrders": stats[STATUS_PICKED_UP],
            "cancelledOrders": stats[STATUS_CANCELLED],
            "totalRevenue": total_revenue,
            "vipOrders": vip_count,
        })

    except Exception:
        logger.exception("Unexpected error in stand_stats")
        return internal_error()
