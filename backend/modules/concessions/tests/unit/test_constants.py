"""Unit tests for concessions constants."""

from common.constants import (
    VALID_STATUSES,
    VALID_TRANSITIONS,
    STATUS_PENDING,
    STATUS_PREPARING,
    STATUS_READY,
    STATUS_PICKED_UP,
    STATUS_CANCELLED,
    VIP_PRIORITY,
    REGULAR_PRIORITY,
)


class TestStatusTransitions:
    def test_pending_can_transition_to_preparing(self) -> None:
        assert STATUS_PREPARING in VALID_TRANSITIONS[STATUS_PENDING]

    def test_pending_can_transition_to_cancelled(self) -> None:
        assert STATUS_CANCELLED in VALID_TRANSITIONS[STATUS_PENDING]

    def test_preparing_can_transition_to_ready(self) -> None:
        assert STATUS_READY in VALID_TRANSITIONS[STATUS_PREPARING]

    def test_ready_can_transition_to_picked_up(self) -> None:
        assert STATUS_PICKED_UP in VALID_TRANSITIONS[STATUS_READY]

    def test_picked_up_is_terminal(self) -> None:
        assert STATUS_PICKED_UP not in VALID_TRANSITIONS

    def test_cancelled_is_terminal(self) -> None:
        assert STATUS_CANCELLED not in VALID_TRANSITIONS

    def test_all_statuses_defined(self) -> None:
        assert len(VALID_STATUSES) == 5


class TestPriority:
    def test_vip_sorts_before_regular(self) -> None:
        assert VIP_PRIORITY < REGULAR_PRIORITY
