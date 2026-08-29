"""Admin event delete Lambda — DELETE /event/{eventId}."""

from __future__ import annotations

from typing import Any

from common.auth import is_admin_authorized
from common.constants import EVENT_PREFIX, METADATA_SK, STATS_SK
from common.dynamodb import delete_item, get_event
from common.logger import logger
from common.responses import forbidden, internal_error, not_found, no_content


@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """API Gateway proxy handler for DELETE /event/{eventId}."""
    try:
        if not is_admin_authorized(event):
            return forbidden("Admin authorization required.")

        event_id = (event.get("pathParameters") or {}).get("eventId", "").strip()
        if not event_id:
            from common.responses import bad_request
            return bad_request("eventId path parameter is required.")

        existing = get_event(event_id)
        if not existing:
            return not_found(f"Event '{event_id}' not found.")

        pk = f"{EVENT_PREFIX}{event_id}"
        delete_item(pk, METADATA_SK)
        delete_item(pk, STATS_SK)

        logger.info("Admin deleted event", extra={"eventId": event_id})
        return no_content()

    except Exception:
        logger.exception("Unexpected error in admin event delete")
        return internal_error()
