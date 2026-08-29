"""DynamoDB operations for the Concessions module."""

from __future__ import annotations

import os
from typing import Any, Optional

import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

from common.constants import (
    EVENT_PREFIX,
    FAN_PREFIX,
    MENU_PREFIX,
    METADATA,
    ORDER_PREFIX,
    STAND_PREFIX,
    QUEUE_SUFFIX,
    STATUS_PENDING,
    STATUS_CANCELLED,
    VIP_PRIORITY,
    REGULAR_PRIORITY,
    GSI1,
    GSI2,
    GSI3,
    VALID_TRANSITIONS,
)
from common.logger import logger


def _get_table():
    table_name = os.environ.get("TABLE_NAME", "ConcessionsTable")
    dynamodb = boto3.resource("dynamodb")
    return dynamodb.Table(table_name)


# ==========================================================================
# Stand Operations
# ==========================================================================


def put_stand(stand: dict[str, Any]) -> None:
    table = _get_table()
    table.put_item(Item=stand)


def get_stand(stand_id: str) -> Optional[dict[str, Any]]:
    table = _get_table()
    response = table.get_item(
        Key={"PK": f"{STAND_PREFIX}{stand_id}", "SK": METADATA}
    )
    return response.get("Item")


def query_stands_for_event(event_id: str) -> list[dict[str, Any]]:
    """Query all stands for an event using GSI3."""
    table = _get_table()
    response = table.query(
        IndexName=GSI3,
        KeyConditionExpression=Key("GSI3PK").eq(f"{EVENT_PREFIX}{event_id}")
        & Key("GSI3SK").begins_with(f"{STAND_PREFIX}"),
    )
    return response.get("Items", [])


# ==========================================================================
# Menu Operations
# ==========================================================================


def put_menu_item(item: dict[str, Any]) -> None:
    table = _get_table()
    table.put_item(Item=item)


def query_menu_items(stand_id: str) -> list[dict[str, Any]]:
    table = _get_table()
    response = table.query(
        KeyConditionExpression=Key("PK").eq(f"{STAND_PREFIX}{stand_id}")
        & Key("SK").begins_with(MENU_PREFIX),
    )
    return response.get("Items", [])


def decrement_inventory(stand_id: str, item_id: str, quantity: int) -> bool:
    """Atomically decrement inventory. Returns False if insufficient stock."""
    table = _get_table()
    try:
        table.update_item(
            Key={"PK": f"{STAND_PREFIX}{stand_id}", "SK": f"{MENU_PREFIX}{item_id}"},
            UpdateExpression="SET inventory = inventory - :qty",
            ConditionExpression="inventory >= :qty",
            ExpressionAttributeValues={":qty": quantity},
        )
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return False
        raise


def restore_inventory(stand_id: str, item_id: str, quantity: int) -> None:
    """Restore inventory when an order is cancelled."""
    table = _get_table()
    table.update_item(
        Key={"PK": f"{STAND_PREFIX}{stand_id}", "SK": f"{MENU_PREFIX}{item_id}"},
        UpdateExpression="SET inventory = inventory + :qty",
        ExpressionAttributeValues={":qty": quantity},
    )


# ==========================================================================
# Order Operations
# ==========================================================================


def put_order(order: dict[str, Any]) -> None:
    table = _get_table()
    table.put_item(Item=order)


def get_order(order_id: str) -> Optional[dict[str, Any]]:
    table = _get_table()
    response = table.get_item(
        Key={"PK": f"{ORDER_PREFIX}{order_id}", "SK": METADATA}
    )
    return response.get("Item")


def put_stand_queue_entry(entry: dict[str, Any]) -> None:
    """Add an order to a stand's queue."""
    table = _get_table()
    table.put_item(Item=entry)


def put_fan_order_entry(entry: dict[str, Any]) -> None:
    """Add a fan order pointer."""
    table = _get_table()
    table.put_item(Item=entry)


def update_order_status_conditional(
    order_id: str,
    current_status: str,
    new_status: str,
    now_iso: str,
    extra_attrs: Optional[dict[str, Any]] = None,
) -> bool:
    """Transition order status with conditional write."""
    if new_status not in VALID_TRANSITIONS.get(current_status, set()):
        return False

    table = _get_table()
    update_expr = "SET #status = :new_status, updatedAt = :now"
    expr_values: dict[str, Any] = {
        ":current": current_status,
        ":new_status": new_status,
        ":now": now_iso,
    }

    if extra_attrs:
        for k, v in extra_attrs.items():
            update_expr += f", {k} = :{k}"
            expr_values[f":{k}"] = v

    try:
        table.update_item(
            Key={"PK": f"{ORDER_PREFIX}{order_id}", "SK": METADATA},
            UpdateExpression=update_expr,
            ConditionExpression="#status = :current",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues=expr_values,
        )
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return False
        raise


def update_stand_queue_entry_status(
    stand_id: str,
    queue_sk: str,
    event_id: str,
    order_id: str,
    new_status: str,
    order_time: str,
    now_iso: str,
) -> None:
    """Update the GSI1 attributes on the stand queue entry for status-based queries."""
    table = _get_table()
    table.update_item(
        Key={
            "PK": f"{STAND_PREFIX}{stand_id}{QUEUE_SUFFIX}",
            "SK": queue_sk,
        },
        UpdateExpression="SET GSI1PK = :gsi1pk, GSI1SK = :gsi1sk, #status = :status, updatedAt = :now",
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues={
            ":gsi1pk": f"{EVENT_PREFIX}{event_id}#{STAND_PREFIX}{stand_id}#STATUS#{new_status}",
            ":gsi1sk": f"{order_time}#{order_id}",
            ":status": new_status,
            ":now": now_iso,
        },
    )


# ==========================================================================
# Stand Queue Queries
# ==========================================================================


def query_stand_queue(stand_id: str, limit: int = 50) -> list[dict[str, Any]]:
    """Get orders in a stand's queue, sorted by order time (FIFO)."""
    table = _get_table()
    response = table.query(
        KeyConditionExpression=Key("PK").eq(
            f"{STAND_PREFIX}{stand_id}{QUEUE_SUFFIX}"
        )
        & Key("SK").begins_with(f"{ORDER_PREFIX}"),
        Limit=limit,
    )
    return response.get("Items", [])


def query_stand_queue_by_status(
    event_id: str, stand_id: str, status: str, limit: int = 50
) -> list[dict[str, Any]]:
    """Get orders for a stand filtered by status, sorted by wait time (GSI1)."""
    table = _get_table()
    response = table.query(
        IndexName=GSI1,
        KeyConditionExpression=Key("GSI1PK").eq(
            f"{EVENT_PREFIX}{event_id}#{STAND_PREFIX}{stand_id}#STATUS#{status}"
        ),
        Limit=limit,
    )
    return response.get("Items", [])


# ==========================================================================
# Fan Order Queries
# ==========================================================================


def query_fan_orders(event_id: str, fan_id: str) -> list[dict[str, Any]]:
    """Get all orders for a fan at an event (GSI2)."""
    table = _get_table()
    response = table.query(
        IndexName=GSI2,
        KeyConditionExpression=Key("GSI2PK").eq(
            f"{EVENT_PREFIX}{event_id}#{FAN_PREFIX}{fan_id}"
        ),
    )
    return response.get("Items", [])


# ==========================================================================
# Analytics / Stats
# ==========================================================================


def query_event_orders(event_id: str, stand_id: Optional[str] = None, limit: int = 500) -> list[dict[str, Any]]:
    """Query orders for an event, optionally filtered by stand (GSI3)."""
    table = _get_table()
    kce = Key("GSI3PK").eq(f"{EVENT_PREFIX}{event_id}")
    if stand_id:
        kce = kce & Key("GSI3SK").begins_with(f"{STAND_PREFIX}{stand_id}#")

    response = table.query(
        IndexName=GSI3,
        KeyConditionExpression=kce,
        Limit=limit,
    )
    return response.get("Items", [])


# ==========================================================================
# Batch Write (stand setup)
# ==========================================================================


def batch_write_items(items: list[dict[str, Any]]) -> None:
    table = _get_table()
    with table.batch_writer() as batch:
        for item in items:
            batch.put_item(Item=item)


# ==========================================================================
# Stand Proximity
# ==========================================================================


def find_closest_stand_with_inventory(
    stands: list[dict[str, Any]],
    fan_section: str,
    ordered_items: list[dict[str, str]],
) -> Optional[dict[str, Any]]:
    """Find the closest stand to the fan's section that has all ordered items in stock.

    Stands have a 'coveredSections' list. A stand covering the fan's section is
    preferred (distance 0). Otherwise, pick by sectionDistance attribute.
    """
    # Score each stand by proximity
    scored_stands = []
    for stand in stands:
        covered = stand.get("coveredSections", [])
        if fan_section in covered:
            distance = 0
        else:
            distance = stand.get("sectionDistance", {}).get(fan_section, 999)
        scored_stands.append((distance, stand))

    scored_stands.sort(key=lambda x: x[0])

    for _, stand in scored_stands:
        # Check inventory for all ordered items
        stand_id = stand.get("standId", "")
        menu_items = query_menu_items(stand_id)
        menu_lookup = {m["itemId"]: int(m.get("inventory", 0)) for m in menu_items}

        all_in_stock = True
        for oi in ordered_items:
            needed = int(oi.get("quantity", 1))
            available = menu_lookup.get(oi.get("itemId", ""), 0)
            if available < needed:
                all_in_stock = False
                break

        if all_in_stock:
            return stand

    return None
