"""Unit tests for leaderboard utilities."""

import pytest
from common.constants import MAX_SCORE_BASE
from common.utils import invert_score, get_shard_id


class TestScoreInversion:
    def test_invert_score_basic(self) -> None:
        result = invert_score(500)
        expected = MAX_SCORE_BASE - 500
        assert result == f"{expected:010d}"

    def test_invert_score_zero(self) -> None:
        result = invert_score(0)
        assert result == str(MAX_SCORE_BASE).zfill(10)

    def test_invert_score_negative_raises(self) -> None:
        with pytest.raises(ValueError):
            invert_score(-1)

    def test_invert_score_too_large_raises(self) -> None:
        with pytest.raises(ValueError):
            invert_score(MAX_SCORE_BASE)

    def test_lexicographical_sorting(self) -> None:
        """Higher scores should result in lexicographically smaller strings."""
        s100 = invert_score(100)
        s500 = invert_score(500)
        s1000 = invert_score(1000)

        # 1000 > 500 > 100
        # Inverted: s1000 < s500 < s100
        assert s1000 < s500
        assert s500 < s100


class TestSharding:
    def test_shard_id_is_deterministic(self) -> None:
        assert get_shard_id("user1") == get_shard_id("user1")

    def test_shard_id_is_hex(self) -> None:
        result = get_shard_id("user1")
        assert len(result) == 2
        int(result, 16)  # Should not raise
