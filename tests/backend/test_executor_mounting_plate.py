"""
test_executor_mounting_plate.py — Intent IR step execution engine tests (F-004)
===============================================================================

The executor walks validated Intent IR steps in order, calling the right handler
for each op (sketch_rectangle, extrude, etc.) and threading shapes between steps.

F-004 defines the execution engine. These tests cover handler registration,
stub ops, dependency errors, end-to-end golden path, and JSON-RPC wiring.

Beginner concepts:
  - Handler registry: maps op names like "extrude" to Python functions.
  - ExecutionResult: success flag, step_ids completed, shapes_by_step_id map.
  - dispatch: jsonrpcserver routes execute_intent RPC calls to the executor.
"""

import json

import pytest

import main  # noqa: F401 — registers JSON-RPC methods on import

from engine.errors import StepNotImplementedError
from engine.executor import execute_intent_ir
from engine.handler_registry import get_handler, registered_ops
from ir.validator import IntentIRValidationError, validate_intent_ir
from jsonrpcserver import dispatch
from project.export import export_step_file
from schemas.intent_ir import IRStep, IRTarget, IntentIR, MVP_STEP_OPS

from test_intent_ir_validation import mounting_plate_ir


def test_handler_registry_covers_mvp_step_ops():
    """Every MVP step op must have a callable handler in the registry."""
    for op in MVP_STEP_OPS:
        handler = get_handler(op)
        assert callable(handler)
    assert registered_ops() == MVP_STEP_OPS


def test_stub_op_returns_step_not_implemented():
    """
    fillet is registered but not implemented — executor should fail gracefully
    with a 'not implemented' message instead of crashing.
    """
    ir_data = {
        "type": "part_create",
        "prompt": "fillet edges",
        "summary": "fillet test",
        "target": {"part_id": "test_part"},
        "steps": [
            {
                "id": "s1",
                "op": "fillet",
                "params": {"radius": 1.0},
            }
        ],
    }
    intent = validate_intent_ir(ir_data)
    result = execute_intent_ir(intent)
    assert not result.success
    assert "not implemented" in (result.error or "").lower()


def test_missing_from_dependency_fails_before_geometry():
    """
    An extrude step without a 'from' reference should fail before touching OCCT.
    model_construct bypasses validation to test runtime dependency checks.
    """
    intent = IntentIR.model_construct(
        type="part_create",
        prompt="bad extrude",
        summary="missing from",
        target=IRTarget(part_id="p1"),
        steps=[
            IRStep.model_construct(
                id="s2",
                op="extrude",
                params={"distance": 6.0, "direction": "+Z", "mode": "add"},
                from_step=None,
            )
        ],
    )
    result = execute_intent_ir(intent)
    assert not result.success
    assert "from" in (result.error or "").lower()


def test_mounting_plate_ir_executes_end_to_end():
    """Golden path: all three steps run and produce shapes keyed by step id."""
    pytest.importorskip("OCC.Core.TopoDS")

    intent = validate_intent_ir(mounting_plate_ir())
    result = execute_intent_ir(intent)

    assert result.success
    assert result.final_step_id == "s3"
    assert result.step_ids == ["s1", "s2", "s3"]
    assert "s3" in result.shapes_by_step_id


def test_mounting_plate_exports_step(tmp_path):
    """After execution, the final shape should export to a non-empty STEP file."""
    pytest.importorskip("OCC.Core.TopoDS")
    from kernel.occt_bridge import read_step

    intent = validate_intent_ir(mounting_plate_ir())
    result = execute_intent_ir(intent)
    assert result.success

    final_shape = result.shapes_by_step_id[result.final_step_id]
    step_path = tmp_path / "mounting_plate.step"
    export_step_file(final_shape, step_path)

    assert step_path.is_file()
    assert step_path.stat().st_size > 0
    imported = read_step(step_path)
    assert not imported.IsNull()


def test_execute_intent_jsonrpc_success():
    """execute_intent RPC should return success with final_step_id s3."""
    pytest.importorskip("OCC.Core.TopoDS")

    request = json.dumps(
        {
            "jsonrpc": "2.0",
            "method": "execute_intent",
            "params": {"ir": mounting_plate_ir()},
            "id": 1,
        }
    )
    response = json.loads(dispatch(request))
    assert response["result"]["success"] is True
    assert response["result"]["final_step_id"] == "s3"


def test_execute_intent_jsonrpc_validation_error():
    """Invalid IR sent over RPC should return JSON-RPC error code -32602."""
    bad_ir = mounting_plate_ir()
    del bad_ir["summary"]

    request = json.dumps(
        {
            "jsonrpc": "2.0",
            "method": "execute_intent",
            "params": {"ir": bad_ir},
            "id": 2,
        }
    )
    response = json.loads(dispatch(request))
    assert "error" in response
    assert response["error"]["code"] == -32602


def test_step_not_implemented_error_has_op():
    """StepNotImplementedError should carry the op name for clear error messages."""
    exc = StepNotImplementedError("fillet")
    assert exc.op == "fillet"
    assert "fillet" in str(exc)


def test_validate_intent_ir_rejects_forward_dependency():
    """Steps must not reference a later step (forward dependency is invalid)."""
    data = mounting_plate_ir()
    data["steps"] = [
        {
            "id": "s2",
            "op": "extrude",
            "from": "s3",
            "params": {"distance": 6.0, "direction": "+Z", "mode": "add"},
        },
        {
            "id": "s3",
            "op": "hole_pattern_corners",
            "from": "s2",
            "params": {"diameter": 6.0, "offset": 8.0},
        },
    ]
    with pytest.raises(IntentIRValidationError):
        validate_intent_ir(data)
