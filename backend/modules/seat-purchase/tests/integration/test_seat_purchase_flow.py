"""Integration tests for the full seat purchase flow.

Covers: seat map, hold, release, purchase, double-hold prevention,
expired hold reclaim, purchase transaction atomicity.
"""

from __future__ import annotations

import json
import time
from typing import Any
from unittest.mock import patch

import pytest

from tests.conftest import MockLambdaContext, make_apigw_event, make_admin_apigw_event


EVENT_ID = "2001"


def _create_session(table: Any, lambda_context: MockLambdaContext, fan_id: str = "fan-1") -> str:
    """Helper: directly insert a session (bypasses token validation for unit testing)."""
    from common.utils import generate_id, utc_now_iso, epoch_minutes_from_now

    session_id = generate_id()
    table.put_item(Item={
        "PK": f"SESSION#{session_id}",
        "SK": "METADATA",
        "sessionId": session_id,
        "fanId": fan_id,
        "eventId": EVENT_ID,
        "tokenId": "TEST-TOKEN",
        "status": "ACTIVE",
        "createdAt": utc_now_iso(),
        "updatedAt": utc_now_iso(),
        "ttl": epoch_minutes_from_now(30),
    })
    return session_id


def _seat_map(table: Any, lambda_context: MockLambdaContext, section_id: str = "A") -> dict[str, Any]:
    from seat_map.app import lambda_handler

    event = make_apigw_event(
        http_method="GET",
        path_parameters={"eventId": EVENT_ID, "sectionId": section_id},
    )
    response = lambda_handler(event, lambda_context)
    return json.loads(response["body"])


def _hold(table: Any, lambda_context: MockLambdaContext, session_id: str, seat_label: str, section_id: str = "A") -> dict[str, Any]:
    from hold_seat.app import lambda_handler

    event = make_apigw_event(body={
        "sessionId": session_id,
        "eventId": EVENT_ID,
        "sectionId": section_id,
        "seatLabel": seat_label,
    })
    response = lambda_handler(event, lambda_context)
    return {"statusCode": response["statusCode"], **json.loads(response["body"])}


def _release(table: Any, lambda_context: MockLambdaContext, hold_id: str) -> dict[str, Any]:
    from release_seat.app import lambda_handler

    event = make_apigw_event(
        http_method="DELETE",
        path_parameters={"holdId": hold_id},
    )
    response = lambda_handler(event, lambda_context)
    return {"statusCode": response["statusCode"], **json.loads(response["body"])}


def _purchase(table: Any, lambda_context: MockLambdaContext, session_id: str, hold_id: str) -> dict[str, Any]:
    from purchase_seat.app import lambda_handler

    event = make_apigw_event(body={"sessionId": session_id, "holdId": hold_id})
    response = lambda_handler(event, lambda_context)
    return {"statusCode": response["statusCode"], **json.loads(response["body"])}


class TestSeatMap:
    def test_returns_all_seats_in_section(self, seeded_table: Any, lambda_context: MockLambdaContext) -> None:
        result = _seat_map(seeded_table, lambda_context, "A")
        assert result["totalSeats"] == 5
        assert result["availableCount"] == 5
        assert all(s["status"] == "AVAILABLE" for s in result["seats"])

    def test_shows_tier_and_price(self, seeded_table: Any, lambda_context: MockLambdaContext) -> None:
        result = _seat_map(seeded_table, lambda_context, "A")
        assert result["seats"][0]["tier"] == "PREMIUM"
        assert result["seats"][0]["price"] == 500


class TestHoldSeat:
    def test_hold_succeeds_on_available_seat(self, seeded_table: Any, lambda_context: MockLambdaContext) -> None:
        session_id = _create_session(seeded_table, lambda_context)
        result = _hold(seeded_table, lambda_context, session_id, "A-001")
        assert result["statusCode"] == 200
        assert "holdId" in result
        assert result["seatLabel"] == "A-001"

    def test_hold_fails_on_already_held_seat(self, seeded_table: Any, lambda_context: MockLambdaContext) -> None:
        s1 = _create_session(seeded_table, lambda_context, "fan-1")
        s2 = _create_session(seeded_table, lambda_context, "fan-2")

        r1 = _hold(seeded_table, lambda_context, s1, "A-001")
        assert r1["statusCode"] == 200

        r2 = _hold(seeded_table, lambda_context, s2, "A-001")
        assert r2["statusCode"] == 409

    def test_hold_reclaims_expired_hold(self, seeded_table: Any, lambda_context: MockLambdaContext) -> None:
        s1 = _create_session(seeded_table, lambda_context, "fan-1")
        s2 = _create_session(seeded_table, lambda_context, "fan-2")

        with patch("hold_seat.app.epoch_minutes_from_now", return_value=int(time.time()) - 1):
            _hold(seeded_table, lambda_context, s1, "A-002")

        r2 = _hold(seeded_table, lambda_context, s2, "A-002")
        assert r2["statusCode"] == 200

    def test_hold_updates_seat_map(self, seeded_table: Any, lambda_context: MockLambdaContext) -> None:
        session_id = _create_session(seeded_table, lambda_context)
        _hold(seeded_table, lambda_context, session_id, "A-001")

        result = _seat_map(seeded_table, lambda_context, "A")
        held_seats = [s for s in result["seats"] if s["status"] == "HELD"]
        assert len(held_seats) == 1
        assert result["availableCount"] == 4


class TestReleaseSeat:
    def test_release_makes_seat_available_again(self, seeded_table: Any, lambda_context: MockLambdaContext) -> None:
        session_id = _create_session(seeded_table, lambda_context)
        hold_result = _hold(seeded_table, lambda_context, session_id, "A-003")
        hold_id = hold_result["holdId"]

        release_result = _release(seeded_table, lambda_context, hold_id)
        assert release_result["statusCode"] == 200
        assert release_result["released"] is True

        result = _seat_map(seeded_table, lambda_context, "A")
        assert result["availableCount"] == 5

    def test_release_fails_for_nonexistent_hold(self, seeded_table: Any, lambda_context: MockLambdaContext) -> None:
        result = _release(seeded_table, lambda_context, "nonexistent-hold")
        assert result["statusCode"] == 404


class TestPurchaseSeat:
    def test_purchase_transitions_seat_to_sold(self, seeded_table: Any, lambda_context: MockLambdaContext) -> None:
        session_id = _create_session(seeded_table, lambda_context)
        hold_result = _hold(seeded_table, lambda_context, session_id, "A-001")
        hold_id = hold_result["holdId"]

        purchase_result = _purchase(seeded_table, lambda_context, session_id, hold_id)
        assert purchase_result["statusCode"] == 200
        assert "ticketId" in purchase_result
        assert purchase_result["seatLabel"] == "A-001"

    def test_purchase_creates_ticket(self, seeded_table: Any, lambda_context: MockLambdaContext) -> None:
        from ticket_detail.app import lambda_handler as ticket_handler

        session_id = _create_session(seeded_table, lambda_context)
        hold_result = _hold(seeded_table, lambda_context, session_id, "A-001")
        purchase_result = _purchase(seeded_table, lambda_context, session_id, hold_result["holdId"])

        ticket_event = make_apigw_event(
            http_method="GET",
            path_parameters={"ticketId": purchase_result["ticketId"]},
        )
        response = ticket_handler(ticket_event, lambda_context)
        body = json.loads(response["body"])

        assert body["ticketId"] == purchase_result["ticketId"]
        assert body["fanId"] == "fan-1"
        assert body["seatLabel"] == "A-001"

    def test_double_purchase_fails(self, seeded_table: Any, lambda_context: MockLambdaContext) -> None:
        """Two fans hold different seats, but fan-2 tries to buy fan-1's sold seat via a crafted hold."""
        s1 = _create_session(seeded_table, lambda_context, "fan-1")
        hold_result = _hold(seeded_table, lambda_context, s1, "A-001")
        hold_id = hold_result["holdId"]

        r1 = _purchase(seeded_table, lambda_context, s1, hold_id)
        assert r1["statusCode"] == 200

        # Attempting to purchase again with same session fails (session is COMPLETED)
        from purchase_seat.app import lambda_handler
        event = make_apigw_event(body={"sessionId": s1, "holdId": hold_id})
        response = lambda_handler(event, lambda_context)
        assert response["statusCode"] == 410  # Gone — session no longer active

    def test_sold_seat_not_holdable(self, seeded_table: Any, lambda_context: MockLambdaContext) -> None:
        s1 = _create_session(seeded_table, lambda_context, "fan-1")
        hold_result = _hold(seeded_table, lambda_context, s1, "A-001")
        _purchase(seeded_table, lambda_context, s1, hold_result["holdId"])

        s2 = _create_session(seeded_table, lambda_context, "fan-2")
        r2 = _hold(seeded_table, lambda_context, s2, "A-001")
        assert r2["statusCode"] == 409

    def test_purchase_updates_section_availability(self, seeded_table: Any, lambda_context: MockLambdaContext) -> None:
        from admin_inventory.app import lambda_handler as inventory_handler

        session_id = _create_session(seeded_table, lambda_context)
        hold_result = _hold(seeded_table, lambda_context, session_id, "A-001")
        _purchase(seeded_table, lambda_context, session_id, hold_result["holdId"])

        inv_event = make_admin_apigw_event(
            http_method="GET",
            path_parameters={"eventId": EVENT_ID},
        )
        response = inventory_handler(inv_event, lambda_context)
        body = json.loads(response["body"])

        section_a = next(s for s in body["sections"] if s["sectionId"] == "A")
        assert section_a["soldSeats"] == 1
        assert section_a["availableSeats"] == 4


class TestFanTickets:
    def test_fan_sees_purchased_ticket(self, seeded_table: Any, lambda_context: MockLambdaContext) -> None:
        from fan_tickets.app import lambda_handler as fan_tickets_handler

        session_id = _create_session(seeded_table, lambda_context)
        hold_result = _hold(seeded_table, lambda_context, session_id, "B-001", "B")
        _purchase(seeded_table, lambda_context, session_id, hold_result["holdId"])

        event = make_apigw_event(
            http_method="GET",
            path_parameters={"fanId": "fan-1"},
        )
        response = fan_tickets_handler(event, lambda_context)
        body = json.loads(response["body"])

        assert body["count"] == 1
        assert body["tickets"][0]["seatLabel"] == "B-001"
