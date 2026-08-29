"""Standard API response builders for the Leaderboard module."""

from __future__ import annotations

import json
from typing import Any


_CORS_HEADERS: dict[str, str] = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": (
        "Content-Type,X-Amz-Date,Authorization,"
        "X-Api-Key,X-Amz-Security-Token,"
        "x-admin-api-key,x-admin-email,x-admin-password"
    ),
    "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
}


def _build_response(status_code: int, body: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": _CORS_HEADERS,
        "body": json.dumps(body, default=str),
    }


def success(body: dict[str, Any]) -> dict[str, Any]:
    return _build_response(200, body)


def created(body: dict[str, Any]) -> dict[str, Any]:
    return _build_response(201, body)


def bad_request(message: str = "Invalid request.") -> dict[str, Any]:
    return _build_response(400, {"error": {"code": "BAD_REQUEST", "message": message}})


def unauthorized(message: str = "Unauthorized.") -> dict[str, Any]:
    return _build_response(401, {"error": {"code": "UNAUTHORIZED", "message": message}})


def forbidden(message: str = "Forbidden.") -> dict[str, Any]:
    return _build_response(403, {"error": {"code": "FORBIDDEN", "message": message}})


def not_found(message: str = "Resource not found.") -> dict[str, Any]:
    return _build_response(404, {"error": {"code": "RESOURCE_NOT_FOUND", "message": message}})


def conflict(message: str = "Resource conflict.") -> dict[str, Any]:
    return _build_response(409, {"error": {"code": "CONFLICT", "message": message}})


def gone(message: str = "Resource expired.") -> dict[str, Any]:
    return _build_response(410, {"error": {"code": "GONE", "message": message}})


def internal_error(message: str = "Internal server error.") -> dict[str, Any]:
    return _build_response(500, {"error": {"code": "INTERNAL_ERROR", "message": message}})
