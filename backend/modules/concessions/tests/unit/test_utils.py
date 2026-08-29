"""Unit tests for concessions utilities."""

import time

from common.utils import (
    compute_shard_id,
    epoch_hours_from_now,
    generate_id,
    generate_order_id,
    parse_body,
    utc_now_epoch,
    utc_now_iso,
    validate_required_fields,
)


class TestTimeUtils:
    def test_utc_now_iso_format(self) -> None:
        result = utc_now_iso()
        assert result.endswith("Z")
        assert "T" in result

    def test_utc_now_epoch_is_recent(self) -> None:
        result = utc_now_epoch()
        assert abs(result - int(time.time())) < 2

    def test_epoch_hours_from_now(self) -> None:
        result = epoch_hours_from_now(2)
        assert result > int(time.time())
        assert abs(result - int(time.time()) - 7200) < 2


class TestIdGeneration:
    def test_generate_id_is_16_chars(self) -> None:
        result = generate_id()
        assert len(result) == 16

    def test_generate_order_id_is_12_uppercase(self) -> None:
        result = generate_order_id()
        assert len(result) == 12
        assert result == result.upper()

    def test_ids_are_unique(self) -> None:
        ids = {generate_id() for _ in range(100)}
        assert len(ids) == 100


class TestParseBody:
    def test_parse_json_string(self) -> None:
        event = {"body": '{"key": "value"}'}
        assert parse_body(event) == {"key": "value"}

    def test_parse_dict(self) -> None:
        event = {"body": {"key": "value"}}
        assert parse_body(event) == {"key": "value"}

    def test_parse_none_body(self) -> None:
        event = {"body": None}
        assert parse_body(event) == {}

    def test_parse_invalid_json(self) -> None:
        event = {"body": "not json"}
        assert parse_body(event) == {}


class TestValidation:
    def test_all_fields_present(self) -> None:
        data = {"a": "1", "b": "2"}
        assert validate_required_fields(data, ["a", "b"]) is None

    def test_missing_fields(self) -> None:
        data = {"a": "1"}
        result = validate_required_fields(data, ["a", "b"])
        assert result is not None
        assert "b" in result


class TestSharding:
    def test_shard_id_is_hex(self) -> None:
        result = compute_shard_id("test-key")
        assert len(result) == 2
        int(result, 16)  # Should not raise

    def test_deterministic(self) -> None:
        a = compute_shard_id("same-key")
        b = compute_shard_id("same-key")
        assert a == b
