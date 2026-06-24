"""JSON-RPC test helpers for backend spec compliance tests."""

from __future__ import annotations

import json
from typing import Any

import main  # noqa: F401 — registers JSON-RPC methods

from jsonrpcserver import dispatch


def call_rpc(method: str, params: dict[str, Any] | None = None, *, req_id: int = 1) -> dict[str, Any]:
    """Dispatch one JSON-RPC request and return the parsed response envelope."""
    request = json.dumps(
        {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": req_id,
        }
    )
    return json.loads(dispatch(request))


def assert_rpc_success(response: dict[str, Any]) -> Any:
    assert "result" in response, f"Expected RPC success, got: {response}"
    assert "error" not in response
    return response["result"]


def assert_rpc_error(response: dict[str, Any]) -> dict[str, Any]:
    assert "error" in response, f"Expected RPC error, got: {response}"
    return response["error"]


def assert_rpc_method_registered(method: str, params: dict[str, Any] | None = None) -> None:
    """Fail clearly when a spec-required JSON-RPC method is not registered."""
    response = call_rpc(method, params)
    if "error" in response:
        message = response["error"].get("message", "")
        if "not found" in message.lower() or "method" in message.lower():
            raise AssertionError(f"JSON-RPC method {method!r} is not registered (F-spec pending)")
    # Any other error means the method exists but params were invalid — that is fine here.
