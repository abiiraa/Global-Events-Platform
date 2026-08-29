"""Constants for the Leaderboard module."""

from __future__ import annotations

# Key prefixes
LB_PREFIX: str = "LB#"
SHARD_PREFIX: str = "SHARD#"
SCORE_PREFIX: str = "SCORE#"
PARTICIPANT_PREFIX: str = "PART#"

# SK constants
METADATA: str = "METADATA"

# Shard counts
SHARD_COUNT: int = 16

# GSI names
GSI1: str = "GSI1"
GSI2: str = "GSI2"

# Dummy index for GSI2 partition key (all leaderboards in one partition for easy listing)
LB_INDEX: str = "LB_INDEX"

# Max score for inversion (10 billion) - ensures lexical sort works correctly for scores up to 9,999,999,999
MAX_SCORE_BASE: int = 10000000000
