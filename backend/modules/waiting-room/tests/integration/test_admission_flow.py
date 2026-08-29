"""Integration tests for the full admission flow.

Covers: batch assignment (batchId), token delivery via status poll,
capacity pause behavior, and completion freeing slots.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from tests.conftest import MockLambdaContext, make_admin_apigw_event, make_apigw_event


def _join(seeded_table: Any, lambda_context: MockLambdaContext, user_id: str) -> dict[str, Any]:
    from join_queue.app import lambda_handler

    event = make_apigw_event(body={"eventId": "1001", "userId": user_id})
    response = lambda_handler(event, lambda_context)
    return json.loads(response["body"])


def _admit(seeded_table: Any, lambda_context: MockLambdaContext, batch_size: int = 50, capacity_mode: bool = False) -> dict[str, Any]:
    from admit_users.app import lambda_handler

    body: dict[str, Any] = {"eventId": "1001", "batchSize": batch_size}
    if capacity_mode:
        body["capacityMode"] = True
        body["purchasingCapacity"] = 2
    event = make_admin_apigw_event(body=body)
    response = lambda_handler(event, lambda_context)
    return json.loads(response["body"])


def _status(seeded_table: Any, lambda_context: MockLambdaContext, user_id: str) -> dict[str, Any]:
    from queue_status.app import lambda_handler

    event = make_apigw_event(
        body=None,
        query_string_parameters={"eventId": "1001", "userId": user_id},
        http_method="GET",
    )
    response = lambda_handler(event, lambda_context)
    return json.loads(response["body"])


def _complete(seeded_table: Any, lambda_context: MockLambdaContext, user_id: str) -> dict[str, Any]:
    from complete_session.app import lambda_handler

    event = make_apigw_event(body={"eventId": "1001", "userId": user_id})
    response = lambda_handler(event, lambda_context)
    return json.loads(response["body"])


class TestBatchAssignment:
    """batchId is persisted on each admitted queue entry."""

    def test_admit_returns_batch_id(self, seeded_table: Any, lambda_context: MockLambdaContext) -> None:
        _join(seeded_table, lambda_context, "fan-1")
        result = _admit(seeded_table, lambda_context, batch_size=1)

        assert "batchId" in result
        assert result["batchId"].startswith("BATCH#1001#")

    def test_batch_id_stored_on_queue_entry(self, seeded_table: Any, lambda_context: MockLambdaContext) -> None:
        _join(seeded_table, lambda_context, "fan-1")
        admit_result = _admit(seeded_table, lambda_context, batch_size=1)

        from common.dynamodb import query_user_queue
        item = query_user_queue("fan-1", "1001")
        assert item["batchId"] == admit_result["batchId"]

    def test_same_batch_id_for_all_users_in_batch(self, seeded_table: Any, lambda_context: MockLambdaContext) -> None:
        _join(seeded_table, lambda_context, "fan-1")
        _join(seeded_table, lambda_context, "fan-2")
        _join(seeded_table, lambda_context, "fan-3")

        admit_result = _admit(seeded_table, lambda_context, batch_size=3)
        batch_id = admit_result["batchId"]

        from common.dynamodb import query_user_queue
        for uid in ["fan-1", "fan-2", "fan-3"]:
            item = query_user_queue(uid, "1001")
            assert item["batchId"] == batch_id

    def test_different_batches_get_different_ids(self, seeded_table: Any, lambda_context: MockLambdaContext) -> None:
        for i in range(4):
            _join(seeded_table, lambda_context, f"fan-{i}")

        r1 = _admit(seeded_table, lambda_context, batch_size=2)
        r2 = _admit(seeded_table, lambda_context, batch_size=2)

        assert r1["batchId"] != r2["batchId"]


class TestTokenDeliveryViaStatus:
    """Fan retrieves tokenId by polling GET /queue/status after admission."""

    def test_waiting_status_has_no_token(self, seeded_table: Any, lambda_context: MockLambdaContext) -> None:
        _join(seeded_table, lambda_context, "fan-1")
        status = _status(seeded_table, lambda_context, "fan-1")

        assert status["status"] == "WAITING"
        assert "tokenId" not in status

    def test_admitted_status_includes_token(self, seeded_table: Any, lambda_context: MockLambdaContext) -> None:
        _join(seeded_table, lambda_context, "fan-1")
        _admit(seeded_table, lambda_context, batch_size=1)

        status = _status(seeded_table, lambda_context, "fan-1")

        assert status["status"] == "ADMITTED"
        assert "tokenId" in status
        assert len(status["tokenId"]) > 0

    def test_token_from_status_is_valid(self, seeded_table: Any, lambda_context: MockLambdaContext) -> None:
        from validate_token.app import lambda_handler as validate_handler

        _join(seeded_table, lambda_context, "fan-1")
        _admit(seeded_table, lambda_context, batch_size=1)
        status = _status(seeded_table, lambda_context, "fan-1")

        token_id = status["tokenId"]
        validate_event = make_apigw_event(body={"token": token_id})
        response = validate_handler(validate_event, lambda_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["valid"] is True
        assert body["userId"] == "fan-1"
        assert body["eventId"] == "1001"

    def test_token_is_single_use(self, seeded_table: Any, lambda_context: MockLambdaContext) -> None:
        from validate_token.app import lambda_handler as validate_handler

        _join(seeded_table, lambda_context, "fan-1")
        _admit(seeded_table, lambda_context, batch_size=1)
        status = _status(seeded_table, lambda_context, "fan-1")
        token_id = status["tokenId"]

        validate_event = make_apigw_event(body={"token": token_id})
        r1 = validate_handler(validate_event, lambda_context)
        assert r1["statusCode"] == 200

        r2 = validate_handler(validate_event, lambda_context)
        assert r2["statusCode"] == 401


class TestCapacityPause:
    """When capacity is full, promotion pauses instead of destroying the queue."""

    def test_capacity_full_returns_pause_not_close(self, seeded_table: Any, lambda_context: MockLambdaContext) -> None:
        for i in range(5):
            _join(seeded_table, lambda_context, f"fan-{i}")

        # Admit 2 with capacity of 2
        r1 = _admit(seeded_table, lambda_context, batch_size=10, capacity_mode=True)
        assert r1["admittedUsers"] == 2
        assert r1["capacityFull"] is True

        # Try to admit more — should get 0 with capacityFull
        r2 = _admit(seeded_table, lambda_context, batch_size=10, capacity_mode=True)
        assert r2["admittedUsers"] == 0
        assert r2["capacityFull"] is True
        assert r2["remainingQueue"] == 3

    def test_waiting_fans_remain_waiting_when_capacity_full(self, seeded_table: Any, lambda_context: MockLambdaContext) -> None:
        for i in range(4):
            _join(seeded_table, lambda_context, f"fan-{i}")

        _admit(seeded_table, lambda_context, batch_size=10, capacity_mode=True)

        # Fans 2 and 3 should still be WAITING
        s2 = _status(seeded_table, lambda_context, "fan-2")
        s3 = _status(seeded_table, lambda_context, "fan-3")
        assert s2["status"] == "WAITING"
        assert s3["status"] == "WAITING"


class TestCompletionFreesCapacity:
    """POST /queue/complete decrements admittedUsers, enabling future admits."""

    def test_complete_decrements_admitted_count(self, seeded_table: Any, lambda_context: MockLambdaContext) -> None:
        _join(seeded_table, lambda_context, "fan-1")
        _admit(seeded_table, lambda_context, batch_size=1)

        from common.dynamodb import get_event_stats
        stats_before = get_event_stats("1001")
        assert int(stats_before["admittedUsers"]) == 1

        _complete(seeded_table, lambda_context, "fan-1")

        stats_after = get_event_stats("1001")
        assert int(stats_after["admittedUsers"]) == 0
        assert int(stats_after["completedUsers"]) == 1

    def test_completion_allows_next_batch(self, seeded_table: Any, lambda_context: MockLambdaContext) -> None:
        for i in range(4):
            _join(seeded_table, lambda_context, f"fan-{i}")

        # Fill capacity (2)
        _admit(seeded_table, lambda_context, batch_size=10, capacity_mode=True)

        # Capacity full — no more admits
        r = _admit(seeded_table, lambda_context, batch_size=10, capacity_mode=True)
        assert r["admittedUsers"] == 0
        assert r["capacityFull"] is True

        # Complete one fan
        _complete(seeded_table, lambda_context, "fan-0")

        # Now one slot is free
        r2 = _admit(seeded_table, lambda_context, batch_size=10, capacity_mode=True)
        assert r2["admittedUsers"] == 1
        assert r2["capacityFull"] is True

    def test_complete_on_non_admitted_fails(self, seeded_table: Any, lambda_context: MockLambdaContext) -> None:
        from complete_session.app import lambda_handler

        _join(seeded_table, lambda_context, "fan-1")
        event = make_apigw_event(body={"eventId": "1001", "userId": "fan-1"})
        response = lambda_handler(event, lambda_context)

        assert response["statusCode"] == 409
