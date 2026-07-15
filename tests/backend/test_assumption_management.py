"""
test_assumption_management.py — Assumption management tests (F-023)
===================================================================

Assumptions are AI guesses the user must confirm, edit, or reject before
modeling proceeds safely. F-023 defines update_assumption — a function and RPC
that mutates assumptions.yaml and clears related problems when confirmed.

Beginner concepts:
  - Assumption: {id, text, scope, source, importance, status} in assumptions.yaml.
  - status: proposed → confirmed | rejected | edited.
  - unresolved_assumption problem: cleared when status becomes confirmed.
"""

from __future__ import annotations

import importlib

import pytest
import yaml

from problems.engine import evaluate_problems
from rpc_helpers import assert_rpc_method_registered, call_rpc, assert_rpc_success
from spec_fixtures import write_assumptions_yaml
from test_intent_ir_validation import mounting_plate_ir
from ir.validator import validate_intent_ir


def _assumptions_module():
    """Import project.assumptions or fail with a clear F-023 pending message."""
    try:
        return importlib.import_module("project.assumptions")
    except ImportError as exc:
        pytest.fail(f"F-023 requires backend/project/assumptions.py: {exc}")


def test_update_assumption_rpc_registered(workspace):
    """update_assumption must be registered as a JSON-RPC method."""
    from project.part_folder import create_part_folder

    create_part_folder(workspace, "mounting_plate")
    assert_rpc_method_registered(
        "update_assumption",
        {
            "workspace_path": str(workspace),
            "part_id": "mounting_plate",
            "assumption_id": "a1",
            "status": "confirmed",
        },
    )


def test_confirming_assumption_updates_yaml(workspace):
    """
    Calling update_assumption with status='confirmed' must persist to assumptions.yaml.
    """
    from project.part_folder import create_part_folder, ASSUMPTIONS_FILENAME

    create_part_folder(workspace, "mounting_plate")
    write_assumptions_yaml(
        workspace,
        "mounting_plate",
        [
            {
                "id": "a1",
                "text": "6 mm holes.",
                "scope": "part",
                "source": "ai",
                "importance": "high",
                "status": "proposed",
            }
        ],
    )

    mod = _assumptions_module()
    update = mod.update_assumption
    update(workspace, "mounting_plate", "a1", status="confirmed")

    data = yaml.safe_load(
        (workspace / "parts" / "mounting_plate" / ASSUMPTIONS_FILENAME).read_text(
            encoding="utf-8"
        )
    )
    a1 = next(a for a in data["assumptions"] if a["id"] == "a1")
    assert a1["status"] == "confirmed"


def test_confirm_clears_unresolved_assumption_problem(workspace):
    """
    After confirming assumption a1, evaluate_problems must not report
    unresolved_assumption for that id.
    """
    mod = _assumptions_module()
    from project.part_folder import create_part_folder

    create_part_folder(workspace, "mounting_plate")
    write_assumptions_yaml(
        workspace,
        "mounting_plate",
        [
            {
                "id": "a1",
                "text": "6 mm holes.",
                "scope": "part",
                "source": "ai",
                "importance": "high",
                "status": "proposed",
            }
        ],
    )
    mod.update_assumption(workspace, "mounting_plate", "a1", status="confirmed")

    ir = mounting_plate_ir()
    ir["assumptions"] = [
        {
            "id": "a1",
            "text": "6 mm holes.",
            "scope": "part",
            "source": "ai",
            "importance": "high",
            "status": "confirmed",
        }
    ]
    intent = validate_intent_ir(ir)
    problems = evaluate_problems(intent)
    assert not any(p.type == "unresolved_assumption" and "a1" in p.id for p in problems)


def test_edit_assumption_text_updates_yaml(workspace):
    """update_assumption with new text must persist the edited text to YAML."""
    mod = _assumptions_module()
    from project.part_folder import create_part_folder, ASSUMPTIONS_FILENAME

    create_part_folder(workspace, "mounting_plate")
    write_assumptions_yaml(
        workspace,
        "mounting_plate",
        [
            {
                "id": "a1",
                "text": "Old text.",
                "scope": "part",
                "source": "ai",
                "importance": "medium",
                "status": "proposed",
            }
        ],
    )
    mod.update_assumption(
        workspace, "mounting_plate", "a1", status="proposed", text="Updated 8 mm holes."
    )
    data = yaml.safe_load(
        (workspace / "parts" / "mounting_plate" / ASSUMPTIONS_FILENAME).read_text(
            encoding="utf-8"
        )
    )
    a1 = next(a for a in data["assumptions"] if a["id"] == "a1")
    assert a1["text"] == "Updated 8 mm holes."


def test_update_assumption_jsonrpc(workspace):
    """update_assumption RPC should succeed for a valid confirm request."""
    from project.part_folder import create_part_folder

    create_part_folder(workspace, "mounting_plate")
    write_assumptions_yaml(
        workspace,
        "mounting_plate",
        [
            {
                "id": "a1",
                "text": "6 mm.",
                "scope": "part",
                "source": "ai",
                "importance": "high",
                "status": "proposed",
            }
        ],
    )
    response = call_rpc(
        "update_assumption",
        {
            "workspace_path": str(workspace),
            "part_id": "mounting_plate",
            "assumption_id": "a1",
            "status": "confirmed",
        },
    )
    assert_rpc_success(response)


def test_invalid_status_rejected(workspace):
    """An invalid status value like 'maybe' must raise an exception."""
    mod = _assumptions_module()
    from project.part_folder import create_part_folder

    create_part_folder(workspace, "mounting_plate")
    with pytest.raises(Exception):
        mod.update_assumption(workspace, "mounting_plate", "a1", status="maybe")
