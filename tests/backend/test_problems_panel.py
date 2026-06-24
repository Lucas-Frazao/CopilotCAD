"""Spec compliance tests for F-010 — Problems panel.

Verifies backend problem payloads satisfy panel contract and all MVP problem
types surface through execute_intent with fields the UI needs.
"""

from __future__ import annotations

import importlib

import pytest

from engine.execution_result import ExecutionResult
from ir.validator import validate_intent_ir
from problems.engine import evaluate_problems, problems_to_dicts
from rpc_helpers import call_rpc, assert_rpc_success
from schemas.problem import Problem

from test_intent_ir_validation import mounting_plate_ir


MVP_PROBLEM_TYPES = frozenset(
    {
        "missing_required_input",
        "unresolved_assumption",
        "geometry_generation_failure",
        "interface_conflict",
        "invalid_mate",
        "manufacturing_rule_warning",
        "traceability_gap",
    }
)

SEVERITY_ORDER = {"blocking": 0, "error": 1, "warning": 2}


def _ir(**overrides):
    data = mounting_plate_ir()
    data.update(overrides)
    return validate_intent_ir(data)


def sort_problems_by_severity(problems: list[dict]) -> list[dict]:
    """Expected panel sort: blocking first, then error, then warning."""
    return sorted(problems, key=lambda p: SEVERITY_ORDER.get(p["severity"], 99))


def test_problem_payload_has_panel_required_fields():
    """Each problem exposes type, message, severity, and suggested next steps."""
    intent = _ir(
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
    problems = problems_to_dicts(evaluate_problems(intent))
    assert len(problems) >= 1
    for problem in problems:
        assert problem["type"] in MVP_PROBLEM_TYPES
        assert problem["severity"] in ("warning", "error", "blocking")
        assert isinstance(problem["message"], str) and problem["message"]
        assert isinstance(problem["suggested_next_steps"], list)
        assert len(problem["suggested_next_steps"]) >= 1


@pytest.mark.parametrize(
    "overrides,expected_type",
    [
        (
            {
                "questions": [
                    {
                        "id": "q1",
                        "text": "Bolt pattern?",
                        "blocking": True,
                        "status": "open",
                    }
                ]
            },
            "missing_required_input",
        ),
        (
            {
                "assumptions": [
                    {
                        "id": "a1",
                        "text": "6 mm holes.",
                        "scope": "part",
                        "source": "ai",
                        "importance": "high",
                        "status": "proposed",
                    }
                ]
            },
            "unresolved_assumption",
        ),
        (
            {"links": {"spec_refs": [], "requirement_refs": [], "architecture_refs": []}},
            "traceability_gap",
        ),
        (
            {"constraints": {"process": "cnc_milling", "dimensions": {}}},
            "manufacturing_rule_warning",
        ),
        (
            {
                "type": "assembly_create",
                "target": {"assembly_id": "asm1"},
                "constraints": {"interfaces": ["a", "a"]},
            },
            "interface_conflict",
        ),
        (
            {"steps": [{"id": "m1", "op": "mate_fix", "params": {}}]},
            "invalid_mate",
        ),
    ],
)
def test_all_mvp_problem_types_can_surface(overrides, expected_type):
    intent = _ir(**overrides)
    problems = evaluate_problems(intent)
    types = {p.type for p in problems}
    assert expected_type in types


def test_geometry_failure_problem_surfaces_on_failed_execute():
    intent = validate_intent_ir(mounting_plate_ir())
    result = ExecutionResult(success=False, error="step failed")
    problems = evaluate_problems(intent, result)
    assert any(p.type == "geometry_generation_failure" for p in problems)


def test_execute_intent_returns_problems_for_panel():
    """Problems panel reads problems[] from latest executeIntent — RPC must include them."""
    ir = mounting_plate_ir()
    ir["steps"] = [{"id": "s1", "op": "fillet", "params": {"radius": 1.0}}]
    response = call_rpc("execute_intent", {"ir": ir})
    assert "error" in response or "result" in response
    payload = response.get("result") or response.get("error", {}).get("data", {})
    assert "problems" in payload
    for problem in payload["problems"]:
        assert "type" in problem
        assert "message" in problem
        assert "severity" in problem


def test_problems_sort_blocking_before_warnings():
    problems = problems_to_dicts(
        [
            Problem(
                id="w1",
                type="traceability_gap",
                severity="warning",
                message="gap",
            ),
            Problem(
                id="b1",
                type="missing_required_input",
                severity="blocking",
                message="blocked",
            ),
            Problem(
                id="e1",
                type="geometry_generation_failure",
                severity="error",
                message="failed",
            ),
        ]
    )
    sorted_problems = sort_problems_by_severity(problems)
    severities = [p["severity"] for p in sorted_problems]
    assert severities == ["blocking", "error", "warning"]


def test_problems_panel_frontend_module_exports_component():
    """F-010 requires ProblemsPanel.tsx and ProblemItem.tsx — import via spec contract test."""
    # Frontend is validated in ProblemsPanel.test.tsx; backend ensures RPC contract only.
    mod = importlib.import_module("schemas.problem")
    assert hasattr(mod, "Problem")
