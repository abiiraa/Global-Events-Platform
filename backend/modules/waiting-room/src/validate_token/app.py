"""
Validate Token Lambda — Validates a user's admission token.

Endpoint: POST /token/validate

This function:
  1. Validates the request body (token required).
  2. Looks up the token item in DynamoDB using the helper function.
  3. Checks if the token exists, is ACTIVE, and has not expired.
  4. Returns the validation decision.
"""

from __future__ import annotations

from typing import Any

from common.constants import TOKEN_ACTIVE, TOKEN_EXPIRED, TOKEN_USED, TOKEN_PREFIX, METADATA_SK
from common.dynamodb import get_token, update_item
from common.logger import logger
from common.responses import bad_request, internal_error, success, unauthorized
from common.utils import parse_body, utc_now_epoch, utc_now_iso, validate_required_fields


@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """API Gateway proxy handler for POST /token/validate."""
    try:
        # ----- Parse & validate -----
        body = parse_body(event)
        validation_error = validate_required_fields(body, ["token"])
        if validation_error:
            return bad_request(validation_error)

        token_id: str = body["token"]

        logger.append_keys(tokenId=token_id)
        logger.info("Processing token validation request")

        # ----- Look up token -----
        token_item = get_token(token_id)
        if not token_item:
            logger.info("Token not found")
            return unauthorized("Token is invalid.")

        status = token_item.get("status", "")
        expires_at = int(token_item.get("expiresAt", 0))
        now_epoch = utc_now_epoch()

        # ----- Validate status and expiration -----
        if status != TOKEN_ACTIVE:
            logger.info(f"Token invalid status: {status}")
            return unauthorized(f"Token is invalid (status: {status}).")

        if now_epoch > expires_at:
            logger.info(f"Token expired. Expires at: {expires_at}, Now: {now_epoch}")
            return unauthorized("Token has expired.")

        # Mark token as consumed — prevents replay
        consumed = update_item(
            pk=f"{TOKEN_PREFIX}{token_id}",
            sk=METADATA_SK,
            update_expression="SET #status = :used, updatedAt = :now",
            expression_values={
                ":used": TOKEN_USED,
                ":now": utc_now_iso(),
                ":active": TOKEN_ACTIVE,
            },
            expression_names={"#status": "status"},
            condition_expression="#status = :active",
        )
        if consumed is None:
            logger.info("Token already consumed or expired between read and update")
            return unauthorized("Token is invalid (already used).")

        logger.info("Token validation successful")

        return success({
            "valid": True,
            "eventId": token_item.get("eventId", ""),
            "userId": token_item.get("userId", ""),
            "expiresAt": expires_at,
        })

    except Exception:
        logger.exception("Unexpected error in validate_token")
        return internal_error()
