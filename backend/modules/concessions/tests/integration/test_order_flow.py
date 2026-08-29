"""Integration tests for the full concession order flow."""

from __future__ import annotations

import json
from typing import Any

import pytest

from tests.conftest import MockLambdaContext, make_apigw_event, make_admin_apigw_event


EVENT_ID = "3001"


def _place_order(
    table: Any,
    lambda_context: MockLambdaContext,
    fan_id: str = "fan-1",
    section: str = "A",
    items: list[dict] | None = None,
    is_vip: bool = False,
) -> dict[str, Any]:
    from place_order.app import lambda_handler

    if items is None:
        items = [{"itemId": "nachos", "name": "Nachos", "quantity": 1, "price": 12}]

    event = make_apigw_event(body={
        "eventId": EVENT_ID,
        "fanId": fan_id,
        "section": section,
        "items": items,
        "isVip": is_vip,
    })
    response = lambda_handler(event, lambda_context)
    return {"statusCode": response["statusCode"], **json.loads(response["body"])}


def _order_status(table: Any, lambda_context: MockLambdaContext, order_id: str) -> dict[str, Any]:
    from order_status.app import lambda_handler

    event = make_apigw_event(
        http_method="GET",
        path_parameters={"orderId": order_id},
    )
    response = lambda_handler(event, lambda_context)
    return {"statusCode": response["statusCode"], **json.loads(response["body"])}


def _update_status(
    table: Any,
    lambda_context: MockLambdaContext,
    order_id: str,
    new_status: str,
) -> dict[str, Any]:
    from update_order_status.app import lambda_handler

    event = make_admin_apigw_event(
        http_method="PUT",
        path_parameters={"orderId": order_id},
        body={"status": new_status},
    )
    response = lambda_handler(event, lambda_context)
    return {"statusCode": response["statusCode"], **json.loads(response["body"])}


def _fan_orders(table: Any, lambda_context: MockLambdaContext, fan_id: str) -> dict[str, Any]:
    from fan_orders.app import lambda_handler

    event = make_apigw_event(
        http_method="GET",
        path_parameters={"fanId": fan_id},
        query_string_parameters={"eventId": EVENT_ID},
    )
    response = lambda_handler(event, lambda_context)
    return {"statusCode": response["statusCode"], **json.loads(response["body"])}


def _stand_queue(
    table: Any,
    lambda_context: MockLambdaContext,
    stand_id: str,
    status: str = "PENDING",
) -> dict[str, Any]:
    from stand_queue.app import lambda_handler

    event = make_apigw_event(
        http_method="GET",
        path_parameters={"standId": stand_id},
        query_string_parameters={"eventId": EVENT_ID, "status": status},
    )
    response = lambda_handler(event, lambda_context)
    return {"statusCode": response["statusCode"], **json.loads(response["body"])}


class TestPlaceOrder:
    def test_order_succeeds_for_covered_section(self, seeded_table: Any, lambda_context: MockLambdaContext) -> None:
        result = _place_order(seeded_table, lambda_context, section="A")
        assert result["statusCode"] == 201
        assert "orderId" in result
        assert result["standId"] == "stand-north"
        assert result["status"] == "PENDING"

    def test_order_routes_to_closest_stand(self, seeded_table: Any, lambda_context: MockLambdaContext) -> None:
        result = _place_order(seeded_table, lambda_context, section="D")
        assert result["statusCode"] == 201
        assert result["standId"] == "stand-south"  # D is covered by south

    def test_order_with_multiple_items(self, seeded_table: Any, lambda_context: MockLambdaContext) -> None:
        items = [
            {"itemId": "nachos", "name": "Nachos", "quantity": 2, "price": 12},
            {"itemId": "hotdog", "name": "Hot Dog", "quantity": 1, "price": 8},
        ]
        result = _place_order(seeded_table, lambda_context, items=items)
        assert result["statusCode"] == 201
        assert result["totalPrice"] == 32  # 12*2 + 8*1

    def test_order_decrements_inventory(self, seeded_table: Any, lambda_context: MockLambdaContext) -> None:
        _place_order(seeded_table, lambda_context, items=[
            {"itemId": "nachos", "name": "Nachos", "quantity": 5, "price": 12},
        ])
        # Verify inventory decreased
        item = seeded_table.get_item(
            Key={"PK": "STAND#stand-north", "SK": "MENU#nachos"}
        )["Item"]
        assert int(item["inventory"]) == 495

    def test_order_fails_with_insufficient_inventory(self, seeded_table: Any, lambda_context: MockLambdaContext) -> None:
        result = _place_order(seeded_table, lambda_context, items=[
            {"itemId": "beer", "name": "Beer", "quantity": 999, "price": 10},
        ])
        assert result["statusCode"] == 409

    def test_order_missing_fields_returns_400(self, seeded_table: Any, lambda_context: MockLambdaContext) -> None:
        from place_order.app import lambda_handler

        event = make_apigw_event(body={"eventId": EVENT_ID})
        response = lambda_handler(event, lambda_context)
        assert response["statusCode"] == 400

    def test_vip_order_creates_successfully(self, seeded_table: Any, lambda_context: MockLambdaContext) -> None:
        result = _place_order(seeded_table, lambda_context, is_vip=True)
        assert result["statusCode"] == 201
        assert result["isVip"] is True


class TestOrderStatus:
    def test_get_existing_order(self, seeded_table: Any, lambda_context: MockLambdaContext) -> None:
        place_result = _place_order(seeded_table, lambda_context)
        order_id = place_result["orderId"]

        status_result = _order_status(seeded_table, lambda_context, order_id)
        assert status_result["statusCode"] == 200
        assert status_result["orderId"] == order_id
        assert status_result["status"] == "PENDING"

    def test_get_nonexistent_order(self, seeded_table: Any, lambda_context: MockLambdaContext) -> None:
        result = _order_status(seeded_table, lambda_context, "nonexistent")
        assert result["statusCode"] == 404


class TestOrderLifecycle:
    def test_full_lifecycle(self, seeded_table: Any, lambda_context: MockLambdaContext) -> None:
        place = _place_order(seeded_table, lambda_context)
        order_id = place["orderId"]

        # PENDING → PREPARING
        r1 = _update_status(seeded_table, lambda_context, order_id, "PREPARING")
        assert r1["statusCode"] == 200
        assert r1["newStatus"] == "PREPARING"

        # PREPARING → READY
        r2 = _update_status(seeded_table, lambda_context, order_id, "READY")
        assert r2["statusCode"] == 200

        # READY → PICKED_UP
        r3 = _update_status(seeded_table, lambda_context, order_id, "PICKED_UP")
        assert r3["statusCode"] == 200

    def test_invalid_transition_returns_409(self, seeded_table: Any, lambda_context: MockLambdaContext) -> None:
        place = _place_order(seeded_table, lambda_context)
        order_id = place["orderId"]

        # PENDING → READY (skipping PREPARING — invalid)
        result = _update_status(seeded_table, lambda_context, order_id, "READY")
        assert result["statusCode"] == 409

    def test_cancel_restores_inventory(self, seeded_table: Any, lambda_context: MockLambdaContext) -> None:
        _place_order(seeded_table, lambda_context, items=[
            {"itemId": "nachos", "name": "Nachos", "quantity": 10, "price": 12},
        ])

        # Check inventory after order
        item_before = seeded_table.get_item(
            Key={"PK": "STAND#stand-north", "SK": "MENU#nachos"}
        )["Item"]
        assert int(item_before["inventory"]) == 490

        # Get the order ID from fan orders
        fan_result = _fan_orders(seeded_table, lambda_context, "fan-1")
        order_id = fan_result["orders"][0]["orderId"]

        # Cancel
        _update_status(seeded_table, lambda_context, order_id, "CANCELLED")

        # Check inventory restored
        item_after = seeded_table.get_item(
            Key={"PK": "STAND#stand-north", "SK": "MENU#nachos"}
        )["Item"]
        assert int(item_after["inventory"]) == 500


class TestFanOrders:
    def test_fan_sees_their_orders(self, seeded_table: Any, lambda_context: MockLambdaContext) -> None:
        _place_order(seeded_table, lambda_context, fan_id="fan-42")
        _place_order(seeded_table, lambda_context, fan_id="fan-42")

        result = _fan_orders(seeded_table, lambda_context, "fan-42")
        assert result["statusCode"] == 200
        assert result["count"] == 2

    def test_fan_with_no_orders(self, seeded_table: Any, lambda_context: MockLambdaContext) -> None:
        result = _fan_orders(seeded_table, lambda_context, "fan-99")
        assert result["statusCode"] == 200
        assert result["count"] == 0


class TestStandQueue:
    def test_stand_shows_pending_orders(self, seeded_table: Any, lambda_context: MockLambdaContext) -> None:
        _place_order(seeded_table, lambda_context, fan_id="fan-1", section="A")
        _place_order(seeded_table, lambda_context, fan_id="fan-2", section="B")

        result = _stand_queue(seeded_table, lambda_context, "stand-north")
        assert result["statusCode"] == 200
        assert result["count"] == 2

    def test_vip_orders_appear_first(self, seeded_table: Any, lambda_context: MockLambdaContext) -> None:
        # Place regular order first
        _place_order(seeded_table, lambda_context, fan_id="fan-regular", section="A", is_vip=False)
        # Then VIP order
        _place_order(seeded_table, lambda_context, fan_id="fan-vip", section="B", is_vip=True)

        result = _stand_queue(seeded_table, lambda_context, "stand-north")
        orders = result["orders"]
        assert len(orders) >= 2
        # VIP should be first (0# sorts before 1#)
        vip_idx = next(i for i, o in enumerate(orders) if o["fanId"] == "fan-vip")
        reg_idx = next(i for i, o in enumerate(orders) if o["fanId"] == "fan-regular")
        assert vip_idx < reg_idx
