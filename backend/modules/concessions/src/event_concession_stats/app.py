"""Event-wide concession analytics for admin dashboard."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from common.auth import is_admin_authorized
from common.constants import (
    STATUS_PENDING,
    STATUS_PREPARING,
    STATUS_READY,
    STATUS_PICKED_UP,
    STATUS_CANCELLED,
)
from common.dynamodb import query_event_orders
from common.logger import logger
from common.responses import bad_request, forbidden, internal_error, success
from common.utils import get_path_parameter


@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    try:
        if not is_admin_authorized(event):
            return forbidden("Admin authorization required.")

        event_id = get_path_parameter(event, "eventId")
        if not event_id:
            return bad_request("Path parameter eventId is required.")

        orders = query_event_orders(event_id, limit=10000)

        # Aggregate stats
        total_revenue = 0
        status_counts: dict[str, int] = defaultdict(int)
        stand_stats: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"orders": 0, "revenue": 0, "items": defaultdict(int)}
        )
        item_popularity: dict[str, int] = defaultdict(int)

        for order in orders:
            status = order.get("status", STATUS_PENDING)
            status_counts[status] += 1
            price = int(order.get("totalPrice", 0))
            total_revenue += price

            stand_id = order.get("standId", "unknown")
            stand_stats[stand_id]["orders"] += 1
            stand_stats[stand_id]["revenue"] += price

            for item in order.get("items", []):
                name = item.get("name", item.get("itemName", "unknown"))
                qty = int(item.get("quantity", 1))
                item_popularity[name] += qty
                stand_stats[stand_id]["items"][name] += qty

        # Top 10 most popular items
        top_items = sorted(item_popularity.items(), key=lambda x: x[1], reverse=True)[:10]

        # Per-stand summary
        per_stand = [
            {
                "standId": sid,
                "totalOrders": sdata["orders"],
                "totalRevenue": sdata["revenue"],
                "topItems": sorted(
                    [{"name": k, "quantity": v} for k, v in sdata["items"].items()],
                    key=lambda x: x["quantity"],
                    reverse=True,
                )[:5],
            }
            for sid, sdata in stand_stats.items()
        ]

        return success({
            "eventId": event_id,
            "totalOrders": len(orders),
            "totalRevenue": total_revenue,
            "statusBreakdown": {
                "pending": status_counts.get(STATUS_PENDING, 0),
                "preparing": status_counts.get(STATUS_PREPARING, 0),
                "ready": status_counts.get(STATUS_READY, 0),
                "completed": status_counts.get(STATUS_PICKED_UP, 0),
                "cancelled": status_counts.get(STATUS_CANCELLED, 0),
            },
            "topItems": [{"name": n, "quantity": q} for n, q in top_items],
            "perStand": per_stand,
        })

    except Exception:
        logger.exception("Unexpected error in event_concession_stats")
        return internal_error()
