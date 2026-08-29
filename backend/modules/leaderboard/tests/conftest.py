"""Shared pytest fixtures for the Leaderboard test suite."""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Generator

import boto3
import pytest
from moto import mock_aws

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


TABLE_NAME = "LeaderboardTable"


@pytest.fixture(autouse=True)
def _set_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TABLE_NAME", TABLE_NAME)
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
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
    """Table pre-seeded with 1 leaderboard."""
    now = "2026-08-01T12:00:00Z"
    
    dynamodb_table.put_item(Item={
        "PK": "LB#lb-1",
        "SK": "METADATA",
        "entityType": "LEADERBOARD",
        "leaderboardId": "lb-1",
        "name": "Global Sprint",
        "type": "standard",
        "createdAt": now,
        "GSI2PK": "LB_INDEX",
        "GSI2SK": f"{now}#lb-1",
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
