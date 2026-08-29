"""Unit tests for concessions response builders."""

import json

from common.responses import success, created, bad_request, not_found, conflict, forbidden, internal_error


class TestResponses:
    def test_success_returns_200(self) -> None:
        result = success({"message": "ok"})
        assert result["statusCode"] == 200
        assert json.loads(result["body"])["message"] == "ok"

    def test_created_returns_201(self) -> None:
        result = created({"id": "123"})
        assert result["statusCode"] == 201

    def test_bad_request_returns_400(self) -> None:
        result = bad_request("missing field")
        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert body["error"]["code"] == "BAD_REQUEST"

    def test_not_found_returns_404(self) -> None:
        result = not_found("Order not found")
        assert result["statusCode"] == 404

    def test_conflict_returns_409(self) -> None:
        result = conflict("Out of stock")
        assert result["statusCode"] == 409

    def test_forbidden_returns_403(self) -> None:
        result = forbidden()
        assert result["statusCode"] == 403

    def test_internal_error_returns_500(self) -> None:
        result = internal_error()
        assert result["statusCode"] == 500

    def test_cors_headers_present(self) -> None:
        result = success({"test": True})
        assert result["headers"]["Access-Control-Allow-Origin"] == "*"
        assert "PUT" in result["headers"]["Access-Control-Allow-Methods"]
