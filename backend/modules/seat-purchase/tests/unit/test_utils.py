"""Unit tests for common utilities."""

from __future__ import annotations

import time

from common.utils import (
    epoch_minutes_from_now,
    generate_id,
    parse_body,
    utc_now_epoch,
    utc_now_iso,
    validate_required_fields,
)


class TestUtcNowIso:
    def test_returns_iso_format(self) -> None:
        result = utc_now_iso()
        assert result.endswith("Z")
        assert "T" in result

    def test_format_is_consistent(self) -> None:
        result = utc_now_iso()
        assert len(result) == 20  # "2026-07-29T12:00:00Z"


class TestUtcNowEpoch:
    def test_returns_integer(self) -> None:
        result = utc_now_epoch()
        assert isinstance(result, int)
        assert result > 1700000000


class TestEpochMinutesFromNow:
    def test_adds_minutes(self) -> None:
        now = int(time.time())
        result = epoch_minutes_from_now(10)
        assert result >= now + 600
        assert result <= now + 602


class TestGenerateId:
    def test_returns_16_char_hex(self) -> None:
        result = generate_id()
        assert len(result) == 16
        int(result, 16)  # should not raise

    def test_unique(self) -> None:
        ids = {generate_id() for _ in range(100)}
        assert len(ids) == 100


class TestParseBody:
    def test_parses_json_string(self) -> None:
        event = {"body": '{"key": "value"}'}
        assert parse_body(event) == {"key": "value"}

    def test_returns_empty_dict_for_none(self) -> None:
        event = {"body": None}
        assert parse_body(event) == {}

    def test_returns_empty_dict_for_invalid_json(self) -> None:
        event = {"body": "not-json"}
        assert parse_body(event) == {}

    def test_passes_through_dict_body(self) -> None:
        event = {"body": {"already": "parsed"}}
        assert parse_body(event) == {"already": "parsed"}


class TestValidateRequiredFields:
    def test_returns_none_when_all_present(self) -> None:
        data = {"a": "1", "b": "2"}
        assert validate_required_fields(data, ["a", "b"]) is None

    def test_returns_error_for_missing_field(self) -> None:
        data = {"a": "1"}
        result = validate_required_fields(data, ["a", "b"])
        assert result is not None
        assert "b" in result

    def test_empty_string_counts_as_missing(self) -> None:
        data = {"a": "1", "b": ""}
        result = validate_required_fields(data, ["a", "b"])
        assert result is not None
