"""Unit tests for constants."""

from common.constants import (
    STATUS_AVAILABLE,
    STATUS_HELD,
    STATUS_SOLD,
    SESSION_ACTIVE,
    SESSION_COMPLETED,
    VALID_TIERS,
)


def test_seat_statuses_are_distinct() -> None:
    statuses = {STATUS_AVAILABLE, STATUS_HELD, STATUS_SOLD}
    assert len(statuses) == 3


def test_session_statuses_are_distinct() -> None:
    assert SESSION_ACTIVE != SESSION_COMPLETED


def test_valid_tiers_contains_expected() -> None:
    assert "PREMIUM" in VALID_TIERS
    assert "STANDARD" in VALID_TIERS
    assert "GENERAL" in VALID_TIERS
    assert len(VALID_TIERS) == 3
