"""Integration tests for leaderboard scoring."""

from __future__ import annotations

import json
from typing import Any

from tests.conftest import MockLambdaContext, make_apigw_event


LB_ID = "lb-1"


def _submit_score(
    table: Any,
    lambda_context: MockLambdaContext,
    participant_id: str,
    score: int,
) -> dict[str, Any]:
    from submit_score.app import lambda_handler

    event = make_apigw_event(body={
        "leaderboardId": LB_ID,
        "participantId": participant_id,
        "participantName": f"Player {participant_id}",
        "score": score,
    })
    response = lambda_handler(event, lambda_context)
    return {"statusCode": response["statusCode"], **json.loads(response["body"])}


def _get_top_n(
    table: Any,
    lambda_context: MockLambdaContext,
    limit: int = 10,
) -> dict[str, Any]:
    from get_top_n.app import lambda_handler

    event = make_apigw_event(
        http_method="GET",
        path_parameters={"leaderboardId": LB_ID},
        query_string_parameters={"limit": str(limit)},
    )
    response = lambda_handler(event, lambda_context)
    return {"statusCode": response["statusCode"], **json.loads(response["body"])}


def _get_rank(
    table: Any,
    lambda_context: MockLambdaContext,
    participant_id: str,
) -> dict[str, Any]:
    from get_rank.app import lambda_handler

    event = make_apigw_event(
        http_method="GET",
        path_parameters={"leaderboardId": LB_ID, "participantId": participant_id},
    )
    response = lambda_handler(event, lambda_context)
    return {"statusCode": response["statusCode"], **json.loads(response["body"])}


class TestLeaderboardFlow:
    def test_submit_and_retrieve_top_n(self, seeded_table: Any, lambda_context: MockLambdaContext) -> None:
        _submit_score(seeded_table, lambda_context, "p1", 100)
        _submit_score(seeded_table, lambda_context, "p2", 200)
        _submit_score(seeded_table, lambda_context, "p3", 150)

        result = _get_top_n(seeded_table, lambda_context, limit=2)
        assert result["statusCode"] == 200
        
        rankings = result["rankings"]
        assert len(rankings) == 2
        assert rankings[0]["participantId"] == "p2"  # 200
        assert rankings[0]["score"] == 200
        assert rankings[1]["participantId"] == "p3"  # 150

    def test_update_score_replaces_old_score(self, seeded_table: Any, lambda_context: MockLambdaContext) -> None:
        _submit_score(seeded_table, lambda_context, "p1", 100)
        _submit_score(seeded_table, lambda_context, "p2", 200)
        
        # p1 beats p2
        _submit_score(seeded_table, lambda_context, "p1", 300)

        result = _get_top_n(seeded_table, lambda_context, limit=10)
        rankings = result["rankings"]
        
        assert len(rankings) == 2
        assert rankings[0]["participantId"] == "p1"
        assert rankings[0]["score"] == 300
        assert rankings[1]["participantId"] == "p2"

    def test_exact_rank_calculation(self, seeded_table: Any, lambda_context: MockLambdaContext) -> None:
        _submit_score(seeded_table, lambda_context, "p1", 100)
        _submit_score(seeded_table, lambda_context, "p2", 200)
        _submit_score(seeded_table, lambda_context, "p3", 150)
        _submit_score(seeded_table, lambda_context, "p4", 250)

        # p4 (250) -> rank 1
        # p2 (200) -> rank 2
        # p3 (150) -> rank 3
        # p1 (100) -> rank 4

        r3 = _get_rank(seeded_table, lambda_context, "p3")
        assert r3["statusCode"] == 200
        assert r3["rank"] == 3
        assert r3["score"] == 150

        r4 = _get_rank(seeded_table, lambda_context, "p4")
        assert r4["rank"] == 1

    def test_negative_score_rejected(self, seeded_table: Any, lambda_context: MockLambdaContext) -> None:
        result = _submit_score(seeded_table, lambda_context, "p1", -50)
        assert result["statusCode"] == 400
