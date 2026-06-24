"""Spec compliance tests for F-012 — Full single-part flow (golden path).

End-to-end backend golden path: chat IR → part artifacts → geometry → export.
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
    """Execute path must create/update parts/mounting_plate/ artifacts."""
    pytest.importorskip("OCC.Core.TopoDS")

    ir = dict(mounting_plate_ir_dict)
    ir["context"] = {"workspace_path": str(workspace), "active_part_id": "mounting_plate"}

    response = call_rpc("execute_intent", {"ir": ir, "workspace_path": str(workspace)})
    # workspace_path param may be added in F-012; fall back to direct folder check after execute.
    if "error" in response and "workspace_path" in str(response):
        response = call_rpc("execute_intent", {"ir": ir})

    result = response.get("result") or response.get("error", {}).get("data", {})
    assert result.get("success") is True or "step_ids" in result

    part_dir = workspace / "parts" / "mounting_plate"
    # F-012: executor writes spec, assumptions, history when missing.
    for filename in (SPEC_FILENAME, ASSUMPTIONS_FILENAME, HISTORY_FILENAME):
        assert (part_dir / filename).is_file(), (
            f"F-012 golden path must write parts/mounting_plate/{filename}"
        )


def test_golden_path_produces_step_export(workspace, mounting_plate_ir_dict):
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
    response = call_rpc("execute_intent", {"ir": mounting_plate_ir_dict})
    payload = response.get("result") or response.get("error", {}).get("data", {})
    assert "problems" in payload
    assert isinstance(payload["problems"], list)


def test_golden_path_history_appended(workspace, mounting_plate_ir_dict):
    """History panel (F-017) depends on execute appending history.json entries."""
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


def test_golden_path_mesh_available_after_execute(workspace_with_mounting_plate, mounting_plate_ir_dict):
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
    response = call_rpc(
        "list_workspace_tree", {"workspace_path": str(workspace_with_mounting_plate)}
    )
    tree = assert_rpc_success(response)

    def _has_part(nodes: list, name: str) -> bool:
        for node in nodes:
            if node.get("path") == f"parts/{name}":
                return True
            if _has_part(node.get("children") or [], name):
                return True
        return False

    assert _has_part(tree, "mounting_plate")
