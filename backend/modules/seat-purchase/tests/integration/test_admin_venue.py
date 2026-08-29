"""Integration tests for admin venue setup."""

from __future__ import annotations

import json
from typing import Any

import pytest

from tests.conftest import MockLambdaContext, make_admin_apigw_event, make_apigw_event


class TestAdminSetupVenue:
    def test_creates_sections_and_seats(self, dynamodb_table: Any, lambda_context: MockLambdaContext) -> None:
        from admin_setup_venue.app import lambda_handler

        event = make_admin_apigw_event(body={
            "eventId": "3001",
            "sections": [
                {"sectionId": "C", "tier": "GENERAL", "price": 80, "seats": ["C-001", "C-002", "C-003"]},
                {"sectionId": "D", "tier": "PREMIUM", "price": 600, "seats": ["D-001", "D-002"]},
            ],
        })
        response = lambda_handler(event, lambda_context)
        body = json.loads(response["body"])

        assert response["statusCode"] == 201
        assert body["sectionsCreated"] == 2
        assert body["totalSeatsCreated"] == 5

    def test_seats_appear_in_seat_map(self, dynamodb_table: Any, lambda_context: MockLambdaContext) -> None:
        from admin_setup_venue.app import lambda_handler as setup_handler
        from seat_map.app import lambda_handler as seat_map_handler

        setup_event = make_admin_apigw_event(body={
            "eventId": "3001",
            "sections": [
                {"sectionId": "E", "tier": "STANDARD", "price": 150, "seats": ["E-001", "E-002"]},
            ],
        })
        setup_handler(setup_event, lambda_context)

        map_event = make_apigw_event(
            http_method="GET",
            path_parameters={"eventId": "3001", "sectionId": "E"},
        )
        response = seat_map_handler(map_event, lambda_context)
        body = json.loads(response["body"])

        assert body["totalSeats"] == 2
        assert body["availableCount"] == 2
        assert body["seats"][0]["tier"] == "STANDARD"
        assert body["seats"][0]["price"] == 150

    def test_rejects_invalid_tier(self, dynamodb_table: Any, lambda_context: MockLambdaContext) -> None:
        from admin_setup_venue.app import lambda_handler

        event = make_admin_apigw_event(body={
            "eventId": "3001",
            "sections": [
                {"sectionId": "X", "tier": "VIP_ULTRA", "price": 9999, "seats": ["X-001"]},
            ],
        })
        response = lambda_handler(event, lambda_context)
        assert response["statusCode"] == 400

    def test_requires_admin_auth(self, dynamodb_table: Any, lambda_context: MockLambdaContext) -> None:
        from admin_setup_venue.app import lambda_handler

        event = make_apigw_event(body={
            "eventId": "3001",
            "sections": [{"sectionId": "Z", "tier": "GENERAL", "price": 50, "seats": ["Z-001"]}],
        })
        response = lambda_handler(event, lambda_context)
        assert response["statusCode"] == 403
