"""Create purchase session by validating a waiting-room admission token."""

from __future__ import annotations

import os
from typing import Any
from urllib.request import Request, urlopen
from urllib.error import URLError
import json

from common.constants import SESSION_PREFIX, METADATA, SESSION_ACTIVE
from common.dynamodb import put_session, get_session
from common.logger import logger
from common.responses import bad_request, conflict, created, internal_error, unauthorized
from common.utils import generate_id, parse_body, utc_now_iso, validate_required_fields, epoch_minutes_from_now


def _validate_token(token_id: str) -> dict[str, Any] | None:
    base_url = os.environ.get("WAITING_ROOM_API_URL", "").rstrip("/")
    if not base_url:
        logger.error("WAITING_ROOM_API_URL not configured")
        return None

    url = f"{base_url}/token/validate"
    payload = json.dumps({"token": token_id}).encode()
    req = Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")

    try:
        with urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read())
            if body.get("valid"):
                return body
            return None
    except URLError:
        logger.exception("Failed to reach waiting-room token/validate")
        return None


@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    try:
        body = parse_body(event)
        error = validate_required_fields(body, ["tokenId", "eventId"])
        if error:
            return bad_request(error)

        token_id = body["tokenId"]
        event_id = body["eventId"]

        token_result = _validate_token(token_id)
        if not token_result:
            return unauthorized("Invalid or expired admission token.")

        if token_result.get("eventId") != event_id:
            return bad_request("Token does not match the requested event.")

        fan_id = token_result["userId"]
        session_id = generate_id()
        now = utc_now_iso()
        ttl = epoch_minutes_from_now(30)

        session_item = {
            "PK": f"{SESSION_PREFIX}{session_id}",
            "SK": METADATA,
            "sessionId": session_id,
            "fanId": fan_id,
            "eventId": event_id,
            "tokenId": token_id,
            "status": SESSION_ACTIVE,
            "createdAt": now,
            "updatedAt": now,
            "ttl": ttl,
        }

        put_session(session_item)

        return created({
            "sessionId": session_id,
            "fanId": fan_id,
            "eventId": event_id,
            "status": SESSION_ACTIVE,
            "expiresAt": ttl,
        })

    except Exception:
        logger.exception("Unexpected error in create_session")
        return internal_error()
