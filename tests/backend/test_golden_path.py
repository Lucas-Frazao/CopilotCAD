"""
test_golden_path.py — Full single-part flow golden path tests (F-012)
=====================================================================

F-012 defines the end-to-end backend golden path:
  chat IR → part artifacts on disk → geometry execution → STEP export → mesh.

These tests stitch together F-004 (executor), F-011 (mesh), F-017 (history),
and F-024 (export) into one coherent user journey.

Beginner concepts:
  - Golden path: the canonical mounting plate flow every integration test reuses.
  - Part artifacts: spec.yaml, assumptions.yaml, history.json under parts/<id>/.
  - execute_intent RPC: the main entry point that runs IR against a workspace.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from project.part_folder import ASSUMPTIONS_FILENAME, HISTORY_FILENAME, SPEC_FILENAME
from rpc_helpers import call_rpc, assert_rpc_success
from spec_fixtures import read_history_events

from test_intent_ir_validation import mounting_plate_ir


def test_golden_path_execute_writes_part_artifacts(workspace, mounting_plate_ir_dict):
    """
    Execute with workspace context must create/update parts/mounting_plate/
    artifact files (spec, assumptions, history).
    """
    pytest.importorskip("OCC.Core.TopoDS")

    ir = dict(mounting_plate_ir_dict)
    ir["context"] = {"workspace_path": str(workspace), "active_part_id": "mounting_plate"}

    response = call_rpc("execute_intent", {"ir": ir, "workspace_path": str(workspace)})
    # Fall back if workspace_path param not yet wired in older builds
    if "error" in response and "workspace_path" in str(response):
        response = call_rpc("execute_intent", {"ir": ir})

    result = response.get("result") or response.get("error", {}).get("data", {})
    assert result.get("success") is True or "step_ids" in result

    part_dir = workspace / "parts" / "mounting_plate"
    for filename in (SPEC_FILENAME, ASSUMPTIONS_FILENAME, HISTORY_FILENAME):
        assert (part_dir / filename).is_file(), (
            f"F-012 golden path must write parts/mounting_plate/{filename}"
        )


def test_golden_path_produces_step_export(workspace, mounting_plate_ir_dict):
    """After execute, export_part should write a .step file into exports/."""
    pytest.importorskip("OCC.Core.TopoDS")

    call_rpc("execute_intent", {"ir": mounting_plate_ir_dict})

    export_mod = pytest.importorskip("project.export_polish", reason="F-024/F-012 export")
    assert hasattr(export_mod, "export_part")

    exports_dir = workspace / "exports"
    exports_dir.mkdir(exist_ok=True)
    export_mod.export_part(workspace, "mounting_plate", format="step")
    step_files = list(exports_dir.glob("mounting_plate*.step")) + list(
        exports_dir.glob("mounting_plate*.stp")
    )
    assert step_files, "F-012 requires STEP in exports/ after golden path"


def test_golden_path_execute_returns_problems_array(mounting_plate_ir_dict):
    """Every execute_intent response must include a problems list (may be empty)."""
    response = call_rpc("execute_intent", {"ir": mounting_plate_ir_dict})
    payload = response.get("result") or response.get("error", {}).get("data", {})
    assert "problems" in payload
    assert isinstance(payload["problems"], list)


def test_golden_path_history_appended(workspace, mounting_plate_ir_dict):
    """
    F-017 depends on execute appending entries to history.json.
    At least one event with timestamp and summary/type must exist after execute.
    """
    pytest.importorskip("OCC.Core.TopoDS")

    part_dir = workspace / "parts" / "mounting_plate"
    part_dir.mkdir(parents=True, exist_ok=True)

    ir = dict(mounting_plate_ir_dict)
    ir["context"] = {"workspace_path": str(workspace), "active_part_id": "mounting_plate"}
    call_rpc("execute_intent", {"ir": ir, "workspace_path": str(workspace)})

    events = read_history_events(workspace, "mounting_plate")
    assert len(events) >= 1, "F-012/F-017: execute must append history.json entries"
    entry = events[-1]
    assert "timestamp" in entry
    assert "summary" in entry or "type" in entry


def test_golden_path_mesh_available_after_execute(
    workspace_with_mounting_plate, mounting_plate_ir_dict
):
    """After execute, get_part_mesh must return a result for viewport loading."""
    pytest.importorskip("OCC.Core.TopoDS")
    call_rpc("execute_intent", {"ir": mounting_plate_ir_dict})

    response = call_rpc(
        "get_part_mesh",
        {
            "workspace_path": str(workspace_with_mounting_plate),
            "part_id": "mounting_plate",
        },
    )
    assert "result" in response, "Golden path must enable viewport mesh load (F-011)"


def test_golden_path_explorer_lists_part_folder(workspace_with_mounting_plate):
    """list_workspace_tree must show parts/mounting_plate after scaffolding."""
    response = call_rpc(
        "list_workspace_tree", {"workspace_path": str(workspace_with_mounting_plate)}
    )
    tree = assert_rpc_success(response)

    def _has_part(nodes: list, name: str) -> bool:
        """Recursively search tree nodes for parts/<name>."""
        for node in nodes:
            if node.get("path") == f"parts/{name}":
                return True
            if _has_part(node.get("children") or [], name):
                return True
        return False

    assert _has_part(tree, "mounting_plate")
