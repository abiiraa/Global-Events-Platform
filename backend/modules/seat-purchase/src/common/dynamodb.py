"""DynamoDB operations for the Seat Purchase module."""

from __future__ import annotations

import os
from typing import Any, Optional

import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

from common.constants import (
    EVENT_PREFIX,
    FAN_PREFIX,
    HOLD_PREFIX,
    METADATA,
    SEAT_PREFIX,
    SECTION_PREFIX,
    SESSION_PREFIX,
    STATUS_AVAILABLE,
    STATUS_HELD,
    STATUS_SOLD,
    SESSION_ACTIVE,
    SESSION_COMPLETED,
    TICKET_PREFIX,
    GSI1,
    GSI2,
)
from common.logger import logger


def _get_table():
    table_name = os.environ.get("TABLE_NAME", "SeatPurchaseTable")
    dynamodb = boto3.resource("dynamodb")
    return dynamodb.Table(table_name)


def _get_client():
    return boto3.client("dynamodb")


# ==========================================================================
# Seat Operations
# ==========================================================================


def query_seats_in_section(event_id: str, section_id: str) -> list[dict[str, Any]]:
    table = _get_table()
    response = table.query(
        KeyConditionExpression=Key("PK").eq(f"{EVENT_PREFIX}{event_id}#{SECTION_PREFIX}{section_id}")
        & Key("SK").begins_with(SEAT_PREFIX),
    )
    return response.get("Items", [])


def hold_seat(
    event_id: str,
    section_id: str,
    seat_label: str,
    hold_id: str,
    fan_id: str,
    session_id: str,
    hold_expires_at: int,
    now_iso: str,
    now_epoch: int,
) -> bool:
    table = _get_table()
    pk = f"{EVENT_PREFIX}{event_id}#{SECTION_PREFIX}{section_id}"
    sk = f"{SEAT_PREFIX}{seat_label}"

    try:
        table.update_item(
            Key={"PK": pk, "SK": sk},
            UpdateExpression=(
                "SET #status = :held, holdId = :holdId, heldByFanId = :fanId, "
                "sessionId = :sessionId, holdExpiresAt = :expires, updatedAt = :now, "
                "GSI2SK = :gsi2sk"
            ),
            ConditionExpression=(
                "(#status = :available) OR "
                "(#status = :held AND holdExpiresAt < :nowEpoch)"
            ),
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":held": STATUS_HELD,
                ":available": STATUS_AVAILABLE,
                ":holdId": hold_id,
                ":fanId": fan_id,
                ":sessionId": session_id,
                ":expires": hold_expires_at,
                ":now": now_iso,
                ":nowEpoch": now_epoch,
                ":gsi2sk": f"STATUS#{STATUS_HELD}#{SECTION_PREFIX}{section_id}#{SEAT_PREFIX}{seat_label}",
            },
        )
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return False
        raise


def release_seat(
    event_id: str,
    section_id: str,
    seat_label: str,
    hold_id: str,
    now_iso: str,
) -> bool:
    table = _get_table()
    pk = f"{EVENT_PREFIX}{event_id}#{SECTION_PREFIX}{section_id}"
    sk = f"{SEAT_PREFIX}{seat_label}"

    try:
        table.update_item(
            Key={"PK": pk, "SK": sk},
            UpdateExpression=(
                "SET #status = :available, updatedAt = :now, "
                "GSI2SK = :gsi2sk "
                "REMOVE holdId, heldByFanId, sessionId, holdExpiresAt"
            ),
            ConditionExpression="#status = :held AND holdId = :holdId",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":available": STATUS_AVAILABLE,
                ":held": STATUS_HELD,
                ":holdId": hold_id,
                ":now": now_iso,
                ":gsi2sk": f"STATUS#{STATUS_AVAILABLE}#{SECTION_PREFIX}{section_id}#{SEAT_PREFIX}{seat_label}",
            },
        )
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return False
        raise


# ==========================================================================
# Hold Metadata
# ==========================================================================


def put_hold(hold: dict[str, Any]) -> None:
    table = _get_table()
    table.put_item(Item=hold)


def get_hold(hold_id: str) -> Optional[dict[str, Any]]:
    table = _get_table()
    response = table.get_item(Key={"PK": f"{HOLD_PREFIX}{hold_id}", "SK": METADATA})
    return response.get("Item")


# ==========================================================================
# Purchase Session
# ==========================================================================


def put_session(session: dict[str, Any]) -> None:
    table = _get_table()
    table.put_item(
        Item=session,
        ConditionExpression="attribute_not_exists(PK)",
    )


def get_session(session_id: str) -> Optional[dict[str, Any]]:
    table = _get_table()
    response = table.get_item(
        Key={"PK": f"{SESSION_PREFIX}{session_id}", "SK": METADATA}
    )
    return response.get("Item")


# ==========================================================================
# Purchase Transaction
# ==========================================================================


def execute_purchase_transaction(
    event_id: str,
    section_id: str,
    seat_label: str,
    hold_id: str,
    session_id: str,
    fan_id: str,
    ticket_id: str,
    ticket_item: dict[str, Any],
    now_iso: str,
) -> bool:
    client = _get_client()
    table_name = os.environ.get("TABLE_NAME", "SeatPurchaseTable")

    seat_pk = f"{EVENT_PREFIX}{event_id}#{SECTION_PREFIX}{section_id}"
    seat_sk = f"{SEAT_PREFIX}{seat_label}"

    try:
        client.transact_write_items(
            TransactItems=[
                {
                    "Update": {
                        "TableName": table_name,
                        "Key": {
                            "PK": {"S": seat_pk},
                            "SK": {"S": seat_sk},
                        },
                        "UpdateExpression": (
                            "SET #status = :sold, ticketId = :ticketId, "
                            "soldToFanId = :fanId, soldAt = :now, updatedAt = :now, "
                            "GSI2SK = :gsi2sk "
                            "REMOVE holdExpiresAt"
                        ),
                        "ConditionExpression": (
                            "#status = :held AND holdId = :holdId AND "
                            "sessionId = :sessionId AND heldByFanId = :fanId"
                        ),
                        "ExpressionAttributeNames": {"#status": "status"},
                        "ExpressionAttributeValues": {
                            ":sold": {"S": STATUS_SOLD},
                            ":held": {"S": STATUS_HELD},
                            ":holdId": {"S": hold_id},
                            ":sessionId": {"S": session_id},
                            ":fanId": {"S": fan_id},
                            ":ticketId": {"S": ticket_id},
                            ":now": {"S": now_iso},
                            ":gsi2sk": {"S": f"STATUS#{STATUS_SOLD}#{SECTION_PREFIX}{section_id}#{SEAT_PREFIX}{seat_label}"},
                        },
                    }
                },
                {
                    "Put": {
                        "TableName": table_name,
                        "Item": _serialize_item(ticket_item),
                        "ConditionExpression": "attribute_not_exists(PK)",
                    }
                },
                {
                    "Put": {
                        "TableName": table_name,
                        "Item": _serialize_item({
                            "PK": f"{FAN_PREFIX}{fan_id}",
                            "SK": f"{EVENT_PREFIX}{event_id}#{TICKET_PREFIX}{ticket_id}",
                            "ticketId": ticket_id,
                            "eventId": event_id,
                            "sectionId": section_id,
                            "seatLabel": seat_label,
                            "purchasedAt": now_iso,
                            "GSI1PK": f"{FAN_PREFIX}{fan_id}",
                            "GSI1SK": f"{EVENT_PREFIX}{event_id}#{TICKET_PREFIX}{ticket_id}",
                        }),
                    }
                },
                {
                    "Update": {
                        "TableName": table_name,
                        "Key": {
                            "PK": {"S": f"{SESSION_PREFIX}{session_id}"},
                            "SK": {"S": METADATA},
                        },
                        "UpdateExpression": "SET #status = :completed, completedAt = :now, ticketId = :ticketId",
                        "ConditionExpression": "#status = :active",
                        "ExpressionAttributeNames": {"#status": "status"},
                        "ExpressionAttributeValues": {
                            ":completed": {"S": SESSION_COMPLETED},
                            ":active": {"S": SESSION_ACTIVE},
                            ":now": {"S": now_iso},
                            ":ticketId": {"S": ticket_id},
                        },
                    }
                },
                {
                    "Update": {
                        "TableName": table_name,
                        "Key": {
                            "PK": {"S": f"{EVENT_PREFIX}{event_id}"},
                            "SK": {"S": f"{SECTION_PREFIX}{section_id}"},
                        },
                        "UpdateExpression": "SET availableSeats = availableSeats - :one, soldSeats = soldSeats + :one",
                        "ExpressionAttributeValues": {
                            ":one": {"N": "1"},
                        },
                    }
                },
            ]
        )
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "TransactionCanceledException":
            logger.warning("Purchase transaction cancelled", extra={"reasons": str(e)})
            return False
        raise


# ==========================================================================
# Tickets
# ==========================================================================


def get_ticket(ticket_id: str) -> Optional[dict[str, Any]]:
    table = _get_table()
    response = table.get_item(
        Key={"PK": f"{TICKET_PREFIX}{ticket_id}", "SK": METADATA}
    )
    return response.get("Item")


def query_fan_tickets(fan_id: str) -> list[dict[str, Any]]:
    table = _get_table()
    response = table.query(
        IndexName=GSI1,
        KeyConditionExpression=Key("GSI1PK").eq(f"{FAN_PREFIX}{fan_id}"),
    )
    return response.get("Items", [])


# ==========================================================================
# Section Availability
# ==========================================================================


def get_section_availability(event_id: str) -> list[dict[str, Any]]:
    table = _get_table()
    response = table.query(
        KeyConditionExpression=Key("PK").eq(f"{EVENT_PREFIX}{event_id}")
        & Key("SK").begins_with(SECTION_PREFIX),
    )
    return response.get("Items", [])


def put_section_availability(item: dict[str, Any]) -> None:
    table = _get_table()
    table.put_item(Item=item)


# ==========================================================================
# Batch Write (venue setup)
# ==========================================================================


def batch_write_items(items: list[dict[str, Any]]) -> None:
    table = _get_table()
    with table.batch_writer() as batch:
        for item in items:
            batch.put_item(Item=item)


# ==========================================================================
# Admin GSI2 query
# ==========================================================================


def query_inventory_by_status(event_id: str, status: Optional[str] = None, limit: int = 100) -> list[dict[str, Any]]:
    table = _get_table()
    kce = Key("GSI2PK").eq(f"{EVENT_PREFIX}{event_id}")
    if status:
        kce = kce & Key("GSI2SK").begins_with(f"STATUS#{status}#")

    response = table.query(
        IndexName=GSI2,
        KeyConditionExpression=kce,
        Limit=limit,
    )
    return response.get("Items", [])


# ==========================================================================
# Helpers
# ==========================================================================


def _serialize_item(item: dict[str, Any]) -> dict[str, dict[str, str]]:
    serialized = {}
    for k, v in item.items():
        if isinstance(v, str):
            serialized[k] = {"S": v}
        elif isinstance(v, (int, float)):
            serialized[k] = {"N": str(v)}
        elif isinstance(v, bool):
            serialized[k] = {"BOOL": v}
    return serialized
