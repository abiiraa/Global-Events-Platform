"""Shared pytest fixtures for the Concessions test suite."""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Generator

import boto3
import pytest
from moto import mock_aws

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


TABLE_NAME = "ConcessionsTable"


@pytest.fixture(autouse=True)
def _set_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TABLE_NAME", TABLE_NAME)
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("ORDER_TTL_HOURS", "2")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("ADMIN_EMAIL", "admin@test.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "admin123")


def _create_table(dynamodb_resource: Any) -> Any:
    table = dynamodb_resource.create_table(
        TableName=TABLE_NAME,
        KeySchema=[
            {"AttributeName": "PK", "KeyType": "HASH"},
            {"AttributeName": "SK", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "PK", "AttributeType": "S"},
            {"AttributeName": "SK", "AttributeType": "S"},
            {"AttributeName": "GSI1PK", "AttributeType": "S"},
            {"AttributeName": "GSI1SK", "AttributeType": "S"},
            {"AttributeName": "GSI2PK", "AttributeType": "S"},
            {"AttributeName": "GSI2SK", "AttributeType": "S"},
            {"AttributeName": "GSI3PK", "AttributeType": "S"},
            {"AttributeName": "GSI3SK", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "GSI1",
                "KeySchema": [
                    {"AttributeName": "GSI1PK", "KeyType": "HASH"},
                    {"AttributeName": "GSI1SK", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "GSI2",
                "KeySchema": [
                    {"AttributeName": "GSI2PK", "KeyType": "HASH"},
                    {"AttributeName": "GSI2SK", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "GSI3",
                "KeySchema": [
                    {"AttributeName": "GSI3PK", "KeyType": "HASH"},
                    {"AttributeName": "GSI3SK", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    table.meta.client.get_waiter("table_exists").wait(TableName=TABLE_NAME)
    return table


@pytest.fixture()
def dynamodb_table() -> Generator[Any, None, None]:
    with mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        table = _create_table(dynamodb)
        yield table


@pytest.fixture()
def seeded_table(dynamodb_table: Any) -> Any:
    """Table pre-seeded with 2 stands, menu items, and section coverage."""
    now = "2026-08-01T12:00:00Z"
    event_id = "3001"

    stands = [
        {
            "standId": "stand-north",
            "standName": "North Food Court",
            "coveredSections": ["A", "B", "C"],
            "sectionDistance": {"D": 1, "E": 2, "F": 3},
            "menu": [
                {"itemId": "nachos", "itemName": "Nachos", "price": 12, "inventory": 500},
                {"itemId": "hotdog", "itemName": "Hot Dog", "price": 8, "inventory": 300},
                {"itemId": "beer", "itemName": "Beer", "price": 10, "inventory": 200},
            ],
        },
        {
            "standId": "stand-south",
            "standName": "South Grill",
            "coveredSections": ["D", "E", "F"],
            "sectionDistance": {"A": 1, "B": 2, "C": 3},
            "menu": [
                {"itemId": "nachos", "itemName": "Nachos", "price": 12, "inventory": 500},
                {"itemId": "burger", "itemName": "Burger", "price": 15, "inventory": 400},
                {"itemId": "soda", "itemName": "Soda", "price": 5, "inventory": 600},
            ],
        },
    ]

    for stand in stands:
        # Stand metadata
        dynamodb_table.put_item(Item={
            "PK": f"STAND#{stand['standId']}",
            "SK": "METADATA",
            "entityType": "STAND",
            "standId": stand["standId"],
            "standName": stand["standName"],
            "eventId": event_id,
            "coveredSections": stand["coveredSections"],
            "sectionDistance": stand["sectionDistance"],
            "menuItemCount": len(stand["menu"]),
            "createdAt": now,
            "GSI3PK": f"EVENT#{event_id}",
            "GSI3SK": f"STAND#{stand['standId']}",
        })

        # Menu items
        for mi in stand["menu"]:
            dynamodb_table.put_item(Item={
                "PK": f"STAND#{stand['standId']}",
                "SK": f"MENU#{mi['itemId']}",
                "entityType": "MENU_ITEM",
                "itemId": mi["itemId"],
                "itemName": mi["itemName"],
                "category": "food",
                "price": mi["price"],
                "inventory": mi["inventory"],
                "standId": stand["standId"],
                "eventId": event_id,
                "createdAt": now,
            })

    return dynamodb_table


def make_apigw_event(
    body: dict[str, Any] | None = None,
    path_parameters: dict[str, str] | None = None,
    query_string_parameters: dict[str, str] | None = None,
    http_method: str = "POST",
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    return {
        "httpMethod": http_method,
        "headers": {"Content-Type": "application/json", **(headers or {})},
        "pathParameters": path_parameters,
        "queryStringParameters": query_string_parameters,
        "body": json.dumps(body) if body else None,
        "requestContext": {"requestId": "test-request-id", "stage": "Prod"},
    }


def make_admin_apigw_event(
    body: dict[str, Any] | None = None,
    path_parameters: dict[str, str] | None = None,
    query_string_parameters: dict[str, str] | None = None,
    http_method: str = "POST",
) -> dict[str, Any]:
    return make_apigw_event(
        body=body,
        path_parameters=path_parameters,
        query_string_parameters=query_string_parameters,
        http_method=http_method,
        headers={"x-admin-email": "admin@test.com", "x-admin-password": "admin123"},
    )


class MockLambdaContext:
    function_name = "test-function"
    memory_limit_in_mb = 256
    invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test-function"
    aws_request_id = "test-request-id-0001"
    log_group_name = "/aws/lambda/test-function"
    log_stream_name = "2026/08/01/[$LATEST]test"

    def get_remaining_time_in_millis(self) -> int:
        return 30000


@pytest.fixture()
def lambda_context() -> MockLambdaContext:
    return MockLambdaContext()
