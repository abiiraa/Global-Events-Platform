"""Unit tests for response helpers."""

import json

from common.responses import (
    bad_request,
    conflict,
    created,
    forbidden,
    gone,
    internal_error,
    not_found,
    success,
    unauthorized,
)


def test_success_returns_200() -> None:
    response = success({"data": "test"})
    assert response["statusCode"] == 200
    assert json.loads(response["body"])["data"] == "test"


def test_created_returns_201() -> None:
    response = created({"id": "abc"})
    assert response["statusCode"] == 201


def test_bad_request_returns_400() -> None:
    response = bad_request("oops")
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert body["error"]["code"] == "BAD_REQUEST"
    assert body["error"]["message"] == "oops"


def test_unauthorized_returns_401() -> None:
    assert unauthorized()["statusCode"] == 401


def test_forbidden_returns_403() -> None:
    assert forbidden()["statusCode"] == 403


def test_not_found_returns_404() -> None:
    assert not_found()["statusCode"] == 404


def test_conflict_returns_409() -> None:
    assert conflict()["statusCode"] == 409


def test_gone_returns_410() -> None:
    assert gone()["statusCode"] == 410


def test_internal_error_returns_500() -> None:
    assert internal_error()["statusCode"] == 500


def test_cors_headers_present() -> None:
    response = success({"ok": True})
    assert "Access-Control-Allow-Origin" in response["headers"]
    assert response["headers"]["Access-Control-Allow-Origin"] == "*"
