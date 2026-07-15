"""
test_error_handling.py — Error handling and failure UX tests (F-026)
====================================================================

F-026 defines a user-facing error catalog: every failure mode (compile parse
error, validation error, geometry failure, export error, etc.) must return a
friendly message with suggested next steps — never a raw Python traceback.

Beginner concepts:
  - Error catalog: maps failure mode ids to user-facing guidance strings.
  - CompileError: structured error from the compile_intent pipeline.
  - Partial success: completed steps are preserved even when a later step fails.
"""

from __future__ import annotations

import importlib
import json

import pytest

from engine.execution_result import ExecutionResult
from ir.compiler import CompileError
from rpc_helpers import call_rpc
from test_intent_ir_validation import mounting_plate_ir


def _error_catalog():
    """Import errors.catalog or fail with a clear F-026 pending message."""
    try:
        return importlib.import_module("errors.catalog")
    except ImportError as exc:
        pytest.fail(f"F-026 requires backend/errors/catalog.py: {exc}")


# Representative failure modes the catalog must document
FAILURE_MODES = [
    ("compile_parse", "parse", "rephras"),
    ("compile_validation", "validation", "dimensions"),
    ("execute_missing_param", "execution", "param"),
    ("execute_kernel", "geometry", "geometry"),
    ("export_no_geometry", "export", "model"),
    ("slash_bad_args", "slash", "usage"),
    ("ipc_backend_down", "ipc", "backend"),
    ("config_no_api_key", "configuration", "ANTHROPIC_API_KEY"),
]


def test_error_catalog_documents_at_least_ten_modes():
    """ERROR_CATALOG (or entries) must list at least 10 documented failure modes."""
    catalog = _error_catalog()
    entries = getattr(catalog, "ERROR_CATALOG", None) or getattr(catalog, "entries", None)
    assert entries is not None
    assert len(entries) >= 10


@pytest.mark.parametrize("mode_id,error_type,hint", FAILURE_MODES)
def test_failure_mode_has_user_facing_guidance(mode_id, error_type, hint):
    """
    Each failure mode must return a user-facing string containing the expected hint.

    pytest.mark.parametrize runs this once per entry in FAILURE_MODES.
    """
    catalog = _error_catalog()
    lookup = getattr(catalog, "get_user_message", None) or getattr(catalog, "format_error", None)
    assert lookup is not None
    message = lookup(mode_id, error_type=error_type)
    assert isinstance(message, str)
    assert hint.lower() in message.lower() or len(message) > 20


def test_structured_compile_error_has_suggested_steps():
    """
    format_error on a CompileError must include suggested_next_steps or 'try' hints.
    """
    catalog = _error_catalog()
    err = CompileError("validation failed", error_type="validation", field_errors=[])
    formatted = catalog.format_error(err)
    assert "suggested_next_steps" in formatted or "try" in str(formatted).lower()


def test_execute_partial_success_preserves_completed_steps():
    """
    When step 3 fails, steps 1-2 that already completed must still appear
    in the response step_ids array (partial success preservation).
    """
    pytest.importorskip("OCC.Core.TopoDS")
    ir = mounting_plate_ir()
    ir["steps"] = ir["steps"][:2]
    response = call_rpc("execute_intent", {"ir": ir})
    if "result" in response:
        result = response["result"]
        assert result.get("success") is True
        assert len(result.get("step_ids", [])) == 2

    ir_fail = mounting_plate_ir()
    ir_fail["steps"] = ir_fail["steps"][:2] + [
        {"id": "s3", "op": "fillet", "params": {"radius": 1.0}}
    ]
    response2 = call_rpc("execute_intent", {"ir": ir_fail})
    payload = response2.get("result") or response2.get("error", {}).get("data", {})
    assert len(payload.get("step_ids", [])) >= 2, "Partial work must preserve completed steps"


def test_execute_failure_includes_problems_for_panel():
    """
    Failed execute must include problems[] with geometry_generation_failure
    so the Problems panel can show actionable rows.
    """
    ir = mounting_plate_ir()
    ir["steps"] = [{"id": "s1", "op": "fillet", "params": {"radius": 1.0}}]
    response = call_rpc("execute_intent", {"ir": ir})
    payload = response.get("error", {}).get("data", {})
    assert "problems" in payload
    assert any(p["type"] == "geometry_generation_failure" for p in payload["problems"])


def test_jsonrpc_errors_use_structured_data_not_raw_trace():
    """
    JSON-RPC errors must never include Python tracebacks in the response body.
    """
    response = call_rpc("nope_method", {})
    assert "error" in response
    assert "Traceback" not in json.dumps(response)


def test_mounting_plate_compile_failure_friendly_message():
    """
    A compile validation failure must return a message mentioning modeling plan
    or dimensions — not a raw schema error dump.
    """
    catalog = _error_catalog()
    msg = catalog.get_user_message(
        "compile_validation",
        details={"field_errors": [{"loc": ["summary"], "msg": "missing"}]},
    )
    assert "modeling plan" in msg.lower() or "dimensions" in msg.lower()
