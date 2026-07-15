"""
rpc_helpers.py — JSON-RPC test helpers
=======================================

CopilotCAD's Python backend speaks JSON-RPC 2.0 over stdio. These helpers let
tests call backend methods the same way the Electron frontend does, without
starting a separate server process.

Used by: most F-0xx spec compliance tests that verify RPC methods are registered
and return the expected shape.

Beginner concepts:
  - JSON-RPC: a simple protocol where you send {"method": "...", "params": {...}}
    and get back {"result": ...} or {"error": ...}.
  - dispatch: the jsonrpcserver function that routes a request to the right handler.
  - Importing `main` registers all RPC handlers as a side effect.
"""

from __future__ import annotations

import json  # Serialize requests and parse response strings
from typing import Any  # Flexible type for RPC params and results

# Importing main registers every JSON-RPC method handler (side effect on import).
# The noqa comment tells linters to ignore "unused import" warnings.
import main  # noqa: F401 — registers JSON-RPC methods

from jsonrpcserver import dispatch  # Routes one JSON-RPC request to its handler


def call_rpc(
    method: str,
    params: dict[str, Any] | None = None,
    *,
    req_id: int = 1,
) -> dict[str, Any]:
    """
    Dispatch one JSON-RPC request and return the parsed response envelope.

    Args:
        method: RPC method name, e.g. "execute_intent" or "list_parts".
        params: Optional parameter dict sent to the handler.
        req_id: Request id echoed back in the response (JSON-RPC convention).

    Returns:
        Parsed response dict — either {"result": ...} or {"error": ...}.
    """
    # Build a JSON-RPC 2.0 request object and serialize it to a string.
    request = json.dumps(
        {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": req_id,
        }
    )
    # dispatch runs the handler synchronously and returns a JSON response string.
    return json.loads(dispatch(request))


def assert_rpc_success(response: dict[str, Any]) -> Any:
    """
    Assert the response is a successful RPC result and return the result payload.

    Fails the test with a clear message if the backend returned an error instead.
    """
    assert "result" in response, f"Expected RPC success, got: {response}"
    assert "error" not in response
    return response["result"]


def assert_rpc_error(response: dict[str, Any]) -> dict[str, Any]:
    """
    Assert the response is an RPC error and return the error object.

    Use this when a test expects the backend to reject invalid input.
    """
    assert "error" in response, f"Expected RPC error, got: {response}"
    return response["error"]


def assert_rpc_method_registered(
    method: str,
    params: dict[str, Any] | None = None,
) -> None:
    """
    Fail clearly when a spec-required JSON-RPC method is not registered.

    Spec compliance tests call this before deeper assertions. If the method
    does not exist, pytest fails with an F-spec pending message instead of a
    cryptic "method not found" later in the test.
    """
    response = call_rpc(method, params)
    if "error" in response:
        message = response["error"].get("message", "")
        # "Method not found" means the feature has not been wired up yet.
        if "not found" in message.lower() or "method" in message.lower():
            raise AssertionError(
                f"JSON-RPC method {method!r} is not registered (F-spec pending)"
            )
    # Any other error means the method exists but our test params were wrong —
    # that is acceptable for a registration check.
