"""
test_problems_engine.py — Problems engine tests (F-006)
========================================================

The problems engine inspects Intent IR (and optional execution results) and
surfaces issues the UI Problems panel can show: unresolved assumptions, missing
inputs, geometry failures, interface conflicts, etc.

F-006 defines problem types and severities. These tests cover each MVP type
and verify problems appear in JSON-RPC execute_intent responses.

Beginner concepts:
  - Problem: typed issue with severity (blocking, error, warning) and message.
  - evaluate_problems: pure function — IR in, list of Problem objects out.
  - problems_to_dicts: serializes Problem models to JSON-friendly dicts.
"""

import json

import pytest

import main  # noqa: F401 — registers JSON-RPC methods

from engine.execution_result import ExecutionResult
from engine.executor import execute_intent_ir
from ir.validator import validate_intent_ir
from jsonrpcserver import dispatch
from problems.engine import evaluate_problems, problems_to_dicts
from schemas.problem import Problem

from test_intent_ir_validation import mounting_plate_ir


def _ir_with(**overrides):
    """Build a validated IntentIR from the golden plate IR with field overrides."""
    data = mounting_plate_ir()
    data.update(overrides)
    return validate_intent_ir(data)


def _has_type(problems: list[Problem], problem_type: str) -> bool:
    """Return True if any problem in the list matches the given type string."""
    return any(p.type == problem_type for p in problems)


def test_evaluate_problems_clean_ir_returns_empty():
    """
    A fully resolved IR with confirmed assumptions and spec refs should
    produce zero problems when execution also succeeded.
    """
    intent = _ir_with(
        assumptions=[
            {
                "id": "a1",
                "text": "Plate thickness is 6 mm.",
                "scope": "part",
                "source": "ai",
                "importance": "medium",
                "status": "confirmed",
            }
        ],
        links={
            "spec_refs": ["mounting_plate"],
            "requirement_refs": [],
            "architecture_refs": [],
        },
    )
    result = ExecutionResult(success=True, step_ids=["s1", "s2", "s3"], final_step_id="s3")
    problems = evaluate_problems(intent, result)
    assert problems == []


def test_missing_required_input():
    """An open blocking question should surface a missing_required_input problem."""
    intent = _ir_with(
        questions=[
            {
                "id": "q1",
                "text": "What bolt pattern?",
                "blocking": True,
                "status": "open",
            }
        ]
    )
    problems = evaluate_problems(intent)
    assert _has_type(problems, "missing_required_input")
    assert problems[0].severity == "blocking"


def test_unresolved_assumption():
    """A proposed (unconfirmed) assumption should surface unresolved_assumption."""
    intent = _ir_with(
        assumptions=[
            {
                "id": "a1",
                "text": "Material is aluminum.",
                "scope": "part",
                "source": "ai",
                "importance": "high",
                "status": "proposed",
            }
        ]
    )
    problems = evaluate_problems(intent)
    assert _has_type(problems, "unresolved_assumption")


def test_geometry_generation_failure():
    """A failed execution result should produce a geometry_generation_failure problem."""
    intent = validate_intent_ir(mounting_plate_ir())
    result = ExecutionResult(success=False, error="step op not implemented: fillet")
    problems = evaluate_problems(intent, result)
    assert _has_type(problems, "geometry_generation_failure")
    assert problems[0].severity == "error"


def test_interface_conflict():
    """Duplicate interface refs in assembly constraints should conflict."""
    intent = _ir_with(
        type="assembly_create",
        target={"assembly_id": "asm1"},
        constraints={
            "interfaces": ["mount_a", "mount_a"],
        },
    )
    problems = evaluate_problems(intent)
    assert _has_type(problems, "interface_conflict")


def test_invalid_mate():
    """An unimplemented mate op (mate_fix) should surface invalid_mate."""
    intent = _ir_with(
        steps=[
            {
                "id": "m1",
                "op": "mate_fix",
                "params": {},
            }
        ]
    )
    problems = evaluate_problems(intent)
    assert _has_type(problems, "invalid_mate")
    assert problems[0].step_id == "m1"


def test_manufacturing_rule_warning():
    """CNC milling without dimensions should warn about manufacturing rules."""
    intent = _ir_with(
        constraints={
            "process": "cnc_milling",
            "dimensions": {},
        }
    )
    problems = evaluate_problems(intent)
    assert _has_type(problems, "manufacturing_rule_warning")


def test_traceability_gap():
    """Empty spec_refs should surface a traceability_gap warning."""
    intent = _ir_with(links={"spec_refs": [], "requirement_refs": [], "architecture_refs": []})
    problems = evaluate_problems(intent)
    assert _has_type(problems, "traceability_gap")


def test_problems_to_dicts_serializes():
    """problems_to_dicts must produce JSON-serializable dicts with a type field."""
    problem = Problem(
        id="traceability_gap:part1",
        type="traceability_gap",
        severity="warning",
        message="gap",
        part_id="part1",
    )
    data = problems_to_dicts([problem])
    assert data[0]["type"] == "traceability_gap"


def test_execute_intent_jsonrpc_includes_problems_on_failure():
    """Failed execute_intent RPC must include problems[] in the error data payload."""
    ir_data = {
        "type": "part_create",
        "prompt": "fillet",
        "summary": "fillet test",
        "target": {"part_id": "test_part"},
        "steps": [{"id": "s1", "op": "fillet", "params": {"radius": 1.0}}],
    }
    request = json.dumps(
        {
            "jsonrpc": "2.0",
            "method": "execute_intent",
            "params": {"ir": ir_data},
            "id": 3,
        }
    )
    response = json.loads(dispatch(request))
    assert "error" in response
    error_data = response["error"]["data"]
    assert "problems" in error_data
    types = {p["type"] for p in error_data["problems"]}
    assert "geometry_generation_failure" in types


def test_execute_intent_jsonrpc_includes_problems_on_success():
    """Successful execute_intent should return an empty problems array."""
    pytest.importorskip("OCC.Core.TopoDS")

    clean_ir = mounting_plate_ir()
    clean_ir["assumptions"] = [
        {
            "id": "a1",
            "text": "Plate thickness is 6 mm.",
            "scope": "part",
            "source": "ai",
            "importance": "medium",
            "status": "confirmed",
        }
    ]
    clean_ir["links"] = {
        "spec_refs": ["mounting_plate"],
        "requirement_refs": [],
        "architecture_refs": [],
    }

    request = json.dumps(
        {
            "jsonrpc": "2.0",
            "method": "execute_intent",
            "params": {"ir": clean_ir},
            "id": 4,
        }
    )
    response = json.loads(dispatch(request))
    assert response["result"]["success"] is True
    assert "problems" in response["result"]
    assert response["result"]["problems"] == []
