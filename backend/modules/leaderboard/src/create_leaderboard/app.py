"""Create a new leaderboard."""

from __future__ import annotations

from typing import Any

from common.auth import is_admin_authorized
from common.constants import LB_INDEX, LB_PREFIX, METADATA
from common.dynamodb import put_leaderboard
from common.logger import logger
from common.responses import bad_request, created, forbidden, internal_error
from common.utils import generate_id, parse_body, utc_now_iso, validate_required_fields


@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    try:
        if not is_admin_authorized(event):
            return forbidden("Admin authorization required.")

        body = parse_body(event)
        error = validate_required_fields(body, ["name"])
        if error:
            return bad_request(error)

        name = body["name"]
        lb_type = body.get("type", "standard")
        lb_id = body.get("leaderboardId") or generate_id()

        now = utc_now_iso()

        lb_item = {
            "PK": f"{LB_PREFIX}{lb_id}",
            "SK": METADATA,
            "entityType": "LEADERBOARD",
            "leaderboardId": lb_id,
            "name": name,
            "type": lb_type,
            "createdAt": now,
            # GSI2 for listing all leaderboards globally, newest first
            "GSI2PK": LB_INDEX,
            "GSI2SK": f"{now}#{lb_id}",
        }
        
        put_leaderboard(lb_item)

        return created({
            "leaderboardId": lb_id,
            "name": name,
            "type": lb_type,
            "createdAt": now,
        })

    except Exception:
        logger.exception("Unexpected error in create_leaderboard")
        return internal_error()
