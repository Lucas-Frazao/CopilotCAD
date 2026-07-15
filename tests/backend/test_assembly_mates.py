"""
test_assembly_mates.py — Assembly mates spec compliance tests (F-019)
======================================================================

Mates constrain how assembly instances relate in 3D space (coincident, concentric,
distance, fixed). F-019 defines four mate ops with real handlers — not stubs.

These tests verify handler registration, execution, invalid-mate problems,
required param validation, and history schema support.

Beginner concepts:
  - Mate: a constraint between two instances (e.g. face A coincident with face B).
  - Handler registry: maps op names to Python functions that apply the constraint.
  - mate_coincident: aligns two faces so they touch in the same plane.
"""

from __future__ import annotations

import importlib

import pytest

from engine.handler_registry import get_handler, registered_ops
from engine.execution_result import ExecutionResult
from ir.validator import validate_intent_ir
from problems.engine import evaluate_problems
from spec_fixtures import assembly_create_ir, make_workspace_with_two_parts, mate_coincident_ir

# All four MVP mate operations F-019 must implement
MATE_OPS = frozenset({"mate_fix", "mate_coincident", "mate_concentric", "mate_distance"})


@pytest.mark.parametrize("op", sorted(MATE_OPS))
def test_mate_ops_registered_in_handler_registry(op):
    """
    Each mate op must have a dedicated handler — not the generic stub handler.

    pytest.mark.parametrize runs this once per op in MATE_OPS.
    """
    handler = get_handler(op)
    assert callable(handler)
    assert handler.__module__ != "engine.step_handlers.stub", (
        f"{op} must have dedicated handler, not stub"
    )


def test_all_four_mate_ops_in_mvp_catalog():
    """All four mate ops must appear in the registered_ops() catalog."""
    assert MATE_OPS.issubset(registered_ops())


def test_valid_two_part_mate_executes():
    """
    A valid mate_coincident IR against a two-part assembly must execute
    successfully and produce a final_shape (requires OCCT).
    """
    pytest.importorskip("OCC.Core.TopoDS")
    workspace = None
    from pathlib import Path
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        workspace = make_workspace_with_two_parts(Path(tmp))
        asm_mod = importlib.import_module("project.assembly_folder")
        asm_mod.create_assembly(
            workspace,
            "demo_asm",
            {
                "id": "demo_asm",
                "name": "Demo",
                "instances": [
                    {"instance_id": "inst_plate", "part_id": "mounting_plate"},
                    {"instance_id": "inst_bracket", "part_id": "bracket"},
                ],
            },
        )

        from engine.executor import execute_intent_ir

        intent = validate_intent_ir(mate_coincident_ir())
        result = execute_intent_ir(intent, workspace_path=workspace)
        assert result.success, result.error
        assert result.final_shape is not None


def test_invalid_mate_produces_problem_not_crash():
    """
    A mate step with empty params should produce an invalid_mate problem,
    not crash the problems engine.
    """
    ir = assembly_create_ir()
    ir["steps"] = [{"id": "m1", "op": "mate_coincident", "params": {}}]
    intent = validate_intent_ir(ir)
    result = ExecutionResult(success=False, error="invalid mate params")
    problems = evaluate_problems(intent, result)
    assert any(p.type == "invalid_mate" for p in problems)


def test_mate_handlers_validate_required_params():
    """Calling a mate handler with empty params must raise an exception."""
    from schemas.intent_ir import IRStep

    for op in MATE_OPS:
        handler = get_handler(op)
        step = IRStep(id="m1", op=op, params={})
        with pytest.raises(Exception):
            handler(step, {})


def test_mate_steps_appear_in_history_schema():
    """History module must support logging mate steps via append_history_entry."""
    hist = pytest.importorskip("project.history")
    assert hasattr(hist, "append_history_entry")
