"""DynamoDB operations for the Leaderboard module."""

from __future__ import annotations

import os
from typing import Any, Optional

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from common.constants import (
    GSI1,
    GSI2,
    LB_INDEX,
    LB_PREFIX,
    METADATA,
    PARTICIPANT_PREFIX,
    SCORE_PREFIX,
    SHARD_COUNT,
    SHARD_PREFIX,
)
from common.logger import logger
from common.utils import get_shard_id, invert_score


def _get_table():
    table_name = os.environ.get("TABLE_NAME", "LeaderboardTable")
    dynamodb = boto3.resource("dynamodb")
    return dynamodb.Table(table_name)


# ==========================================================================
# Leaderboard Management
# ==========================================================================


def put_leaderboard(lb: dict[str, Any]) -> None:
    table = _get_table()
    table.put_item(Item=lb)


def get_leaderboard(lb_id: str) -> Optional[dict[str, Any]]:
    table = _get_table()
    response = table.get_item(Key={"PK": f"{LB_PREFIX}{lb_id}", "SK": METADATA})
    return response.get("Item")


def list_leaderboards(limit: int = 50) -> list[dict[str, Any]]:
    """List all leaderboards, newest first using GSI2."""
    table = _get_table()
    response = table.query(
        IndexName=GSI2,
        KeyConditionExpression=Key("GSI2PK").eq(LB_INDEX),
        ScanIndexForward=False,  # Descending by createdAt
        Limit=limit,
    )
    return response.get("Items", [])


# ==========================================================================
# Score Submission (Transactions)
# ==========================================================================


def submit_score_transaction(
    lb_id: str,
    participant_id: str,
    new_score: int,
    now_iso: str,
    participant_name: str,
    score_data: Optional[dict[str, Any]] = None,
    previous_score: Optional[int] = None,
) -> None:
    """Submit a score atomically. Deletes old shard entry if exists, creates new one, and updates summary."""
    client = boto3.client("dynamodb")
    table_name = os.environ.get("TABLE_NAME", "LeaderboardTable")

    shard_id = get_shard_id(participant_id)
    new_inverted = invert_score(new_score)

    transact_items = []

    # 1. Delete previous score entry in shard (if they had one)
    if previous_score is not None:
        old_inverted = invert_score(previous_score)
        transact_items.append({
            "Delete": {
                "TableName": table_name,
                "Key": {
                    "PK": {"S": f"{LB_PREFIX}{lb_id}#{SHARD_PREFIX}{shard_id}"},
                    "SK": {"S": f"{SCORE_PREFIX}{old_inverted}#{PARTICIPANT_PREFIX}{participant_id}"},
                },
            }
        })

    # 2. Put new score entry in shard
    shard_item = {
        "PK": {"S": f"{LB_PREFIX}{lb_id}#{SHARD_PREFIX}{shard_id}"},
        "SK": {"S": f"{SCORE_PREFIX}{new_inverted}#{PARTICIPANT_PREFIX}{participant_id}"},
        "entityType": {"S": "SCORE_ENTRY"},
        "leaderboardId": {"S": lb_id},
        "participantId": {"S": participant_id},
        "participantName": {"S": participant_name},
        "score": {"N": str(new_score)},
        "updatedAt": {"S": now_iso},
    }
    if score_data:
        # Simplistic conversion for custom data types (assumes flat string map for this challenge)
        shard_item["scoreData"] = {"M": {k: {"S": str(v)} for k, v in score_data.items()}}
        
    transact_items.append({
        "Put": {
            "TableName": table_name,
            "Item": shard_item,
        }
    })

    # 3. Put/Update Participant Summary
    summary_item = {
        "PK": {"S": f"{PARTICIPANT_PREFIX}{participant_id}"},
        "SK": {"S": f"{LB_PREFIX}{lb_id}"},
        "entityType": {"S": "PARTICIPANT_SUMMARY"},
        "participantId": {"S": participant_id},
        "participantName": {"S": participant_name},
        "leaderboardId": {"S": lb_id},
        "score": {"N": str(new_score)},
        "updatedAt": {"S": now_iso},
        # GSI1 for participant profile (all their leaderboards)
        "GSI1PK": {"S": f"{PARTICIPANT_PREFIX}{participant_id}"},
        "GSI1SK": {"S": f"{LB_PREFIX}{lb_id}"},
    }
    if score_data:
        summary_item["scoreData"] = {"M": {k: {"S": str(v)} for k, v in score_data.items()}}

    transact_items.append({
        "Put": {
            "TableName": table_name,
            "Item": summary_item,
        }
    })

    # 4. Upsert Participant Profile metadata
    profile_item = {
        "PK": {"S": f"{PARTICIPANT_PREFIX}{participant_id}"},
        "SK": {"S": METADATA},
        "entityType": {"S": "PARTICIPANT_PROFILE"},
        "participantId": {"S": participant_id},
        "participantName": {"S": participant_name},
        "updatedAt": {"S": now_iso},
    }
    transact_items.append({
        "Put": {
            "TableName": table_name,
            "Item": profile_item,
        }
    })

    client.transact_write_items(TransactItems=transact_items)


# ==========================================================================
# Participant Queries
# ==========================================================================


def get_participant_summary(participant_id: str, lb_id: str) -> Optional[dict[str, Any]]:
    """O(1) lookup of a participant's score on a specific leaderboard."""
    table = _get_table()
    response = table.get_item(
        Key={"PK": f"{PARTICIPANT_PREFIX}{participant_id}", "SK": f"{LB_PREFIX}{lb_id}"}
    )
    return response.get("Item")


def get_participant_profile(participant_id: str) -> Optional[dict[str, Any]]:
    table = _get_table()
    response = table.get_item(
        Key={"PK": f"{PARTICIPANT_PREFIX}{participant_id}", "SK": METADATA}
    )
    return response.get("Item")


def query_participant_leaderboards(participant_id: str) -> list[dict[str, Any]]:
    """Get all leaderboards a participant is on (GSI1)."""
    table = _get_table()
    response = table.query(
        IndexName=GSI1,
        KeyConditionExpression=Key("GSI1PK").eq(f"{PARTICIPANT_PREFIX}{participant_id}")
        & Key("GSI1SK").begins_with(LB_PREFIX),
    )
    return response.get("Items", [])


# ==========================================================================
# Scatter-Gather Leaderboard Queries
# ==========================================================================


def query_top_n_scatter_gather(lb_id: str, n: int) -> list[dict[str, Any]]:
    """Scatter-gather across all shards to find the global top N.
    
    Reads N items from each shard, merges them in memory, and returns the top N.
    """
    table = _get_table()
    results = []

    for shard in range(SHARD_COUNT):
        shard_id = f"{shard:02x}"
        response = table.query(
            KeyConditionExpression=Key("PK").eq(f"{LB_PREFIX}{lb_id}#{SHARD_PREFIX}{shard_id}")
            & Key("SK").begins_with(SCORE_PREFIX),
            Limit=n,
        )
        results.extend(response.get("Items", []))

    # Sort results. The DB SK is SCORE#{inverted}, so lexicographical sort of SK gives highest scores first
    results.sort(key=lambda x: x["SK"])
    return results[:n]


def query_neighbors(lb_id: str, participant_id: str, score: int, limit: int = 5) -> list[dict[str, Any]]:
    """Find records above and below a specific score across all shards."""
    table = _get_table()
    inverted = invert_score(score)
    base_sk = f"{SCORE_PREFIX}{inverted}"

    results = []

    for shard in range(SHARD_COUNT):
        shard_id = f"{shard:02x}"
        pk = f"{LB_PREFIX}{lb_id}#{SHARD_PREFIX}{shard_id}"
        
        # Above (higher scores = lower inverted = lexicographically smaller SK)
        above = table.query(
            KeyConditionExpression=Key("PK").eq(pk) & Key("SK").lte(base_sk),
            ScanIndexForward=False, # Get closest ones
            Limit=limit + 1,
        )
        
        # Below (lower scores = higher inverted = lexicographically larger SK)
        below = table.query(
            KeyConditionExpression=Key("PK").eq(pk) & Key("SK").gt(base_sk),
            Limit=limit,
        )

        results.extend(above.get("Items", []))
        results.extend(below.get("Items", []))

    # Unique and sort
    seen = set()
    unique_results = []
    for r in results:
        # Skip self (might be caught in 'above' if same score)
        if r["participantId"] == participant_id:
            continue
        if r["participantId"] not in seen:
            seen.add(r["participantId"])
            unique_results.append(r)

    unique_results.sort(key=lambda x: x["SK"])

    # Find where the requested score would fall
    # For a real implementation, we'd do a binary search or iterate to find the insertion point
    # Then take `limit` items before and `limit` items after.
    
    # Simple approach for challenge: return all collected neighbors (already bounded by limit per shard)
    # The frontend can format them.
    return unique_results


def calculate_rank(lb_id: str, score: int) -> int:
    """Calculate exact rank via scatter-gather COUNT queries.
    
    Rank is 1 + (number of participants with a strictly higher score).
    Higher score = lower inverted value = lexicographically smaller SK.
    """
    table = _get_table()
    inverted = invert_score(score)
    sk_exclusive_bound = f"{SCORE_PREFIX}{inverted}"
    
    count_higher = 0

    for shard in range(SHARD_COUNT):
        shard_id = f"{shard:02x}"
        response = table.query(
            KeyConditionExpression=Key("PK").eq(f"{LB_PREFIX}{lb_id}#{SHARD_PREFIX}{shard_id}")
            & Key("SK").lt(sk_exclusive_bound),
            Select="COUNT",
        )
        count_higher += response.get("Count", 0)

    return count_higher + 1
