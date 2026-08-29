"""Admin event update Lambda — PUT /event/{eventId}."""

from __future__ import annotations

from typing import Any

from common.auth import is_admin_authorized
from common.constants import EVENT_PREFIX, METADATA_SK
from common.dynamodb import get_event, update_item
from common.logger import logger
from common.responses import bad_request, forbidden, internal_error, not_found, success
from common.utils import parse_body, utc_now_iso


@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """API Gateway proxy handler for PUT /event/{eventId}."""
    try:
        if not is_admin_authorized(event):
            return forbidden("Admin authorization required.")

        event_id = (event.get("pathParameters") or {}).get("eventId", "").strip()
        if not event_id:
            return bad_request("eventId path parameter is required.")

        existing = get_event(event_id)
        if not existing:
            return not_found(f"Event '{event_id}' not found.")

        body = parse_body(event)

        set_parts: list[str] = ["updatedAt = :now"]
        expr_values: dict[str, Any] = {":now": utc_now_iso()}

        if "matchName" in body:
            match_name = str(body["matchName"]).strip()
            if not match_name or len(match_name) > 160:
                return bad_request("matchName cannot be empty or exceed 160 characters.")
            set_parts.append("matchName = :matchName")
            expr_values[":matchName"] = match_name

        if "stadium" in body:
            stadium = str(body["stadium"]).strip()
            if not stadium or len(stadium) > 120:
                return bad_request("stadium cannot be empty or exceed 120 characters.")
            set_parts.append("stadium = :stadium")
            expr_values[":stadium"] = stadium

        if "capacity" in body:
            try:
                capacity = int(body["capacity"])
            except (TypeError, ValueError):
                return bad_request("capacity must be a number.")
            if capacity < 1:
                return bad_request("capacity must be at least 1.")
            set_parts.append("#capacity = :capacity")
            expr_values[":capacity"] = capacity

        if "startTime" in body:
            start_time = str(body["startTime"]).strip()
            if not start_time:
                return bad_request("startTime cannot be empty.")
            set_parts.append("startTime = :startTime")
            expr_values[":startTime"] = start_time

        if "status" in body:
            status = str(body["status"]).strip().upper()
            if status not in {"UPCOMING", "OPEN", "CLOSED", "FINISHED"}:
                return bad_request("status must be UPCOMING, OPEN, CLOSED, or FINISHED.")
            set_parts.append("#status = :status")
            expr_values[":status"] = status

        if "imageUrl" in body:
            set_parts.append("imageUrl = :imageUrl")
            expr_values[":imageUrl"] = str(body["imageUrl"]).strip()

        if "sport" in body:
            set_parts.append("sport = :sport")
            expr_values[":sport"] = str(body["sport"]).strip()

        for price_field in ("vipPrice", "premiumPrice", "standardPrice", "economyPrice"):
            if price_field in body:
                try:
                    set_parts.append(f"{price_field} = :{price_field}")
                    expr_values[f":{price_field}"] = int(body[price_field])
                except (TypeError, ValueError):
                    return bad_request(f"{price_field} must be a number.")

        update_expression = "SET " + ", ".join(set_parts)
        expression_names: dict[str, str] = {}
        if "status" in body:
            expression_names["#status"] = "status"
        if "capacity" in body:
            expression_names["#capacity"] = "capacity"

        updated = update_item(
            pk=f"{EVENT_PREFIX}{event_id}",
            sk=METADATA_SK,
            update_expression=update_expression,
            expression_values=expr_values,
            condition_expression="attribute_exists(PK)",
            expression_names=expression_names or None,
        )
        if updated is None:
            return not_found(f"Event '{event_id}' not found.")

        logger.info("Admin updated event", extra={"eventId": event_id})
        return success({
            "eventId": event_id,
            "matchName": updated.get("matchName"),
            "stadium": updated.get("stadium"),
            "capacity": int(updated.get("capacity", 0)),
            "startTime": updated.get("startTime"),
            "status": updated.get("status"),
        })

    except Exception:
        logger.exception("Unexpected error in admin event update")
        return internal_error()
