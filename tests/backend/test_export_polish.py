"""Spec compliance tests for F-024 — STEP/IGES export polish."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from rpc_helpers import assert_rpc_method_registered, call_rpc
from test_intent_ir_validation import mounting_plate_ir


def _export_module():
    try:
        return importlib.import_module("project.export_polish")
    except ImportError:
        try:
            return importlib.import_module("project.export_service")
        except ImportError as exc:
            pytest.fail(f"F-024 requires project.export_polish or export_service: {exc}")


def test_export_part_rpc_registered(workspace):
    assert_rpc_method_registered(
        "export_part",
        {
            "workspace_path": str(workspace),
            "part_id": "mounting_plate",
            "format": "step",
        },
    )


def test_export_assembly_rpc_registered(workspace):
    assert_rpc_method_registered(
        "export_assembly",
        {
            "workspace_path": str(workspace),
            "assembly_id": "demo_asm",
            "format": "step",
        },
    )


def test_golden_plate_exports_valid_step(workspace, mounting_plate_ir_dict):
    pytest.importorskip("OCC.Core.TopoDS")
    from rpc_helpers import call_rpc

    call_rpc("execute_intent", {"ir": mounting_plate_ir_dict})
    from project.part_folder import create_part_folder

    create_part_folder(workspace, "mounting_plate")

    export_mod = _export_module()
    export_part = export_mod.export_part
    out_path = export_part(workspace, "mounting_plate", format="step")
    assert Path(out_path).is_file()
    assert out_path.suffix.lower() in (".step", ".stp")

    # Read-back via OCCT when available
    bridge = importlib.import_module("kernel.occt_bridge")
    read_step = getattr(bridge, "read_step", None)
    if read_step:
        shape = read_step(out_path)
        assert shape is not None


def test_iges_export(workspace, mounting_plate_ir_dict):
    pytest.importorskip("OCC.Core.TopoDS")
    from rpc_helpers import call_rpc

    call_rpc("execute_intent", {"ir": mounting_plate_ir_dict})
    from project.part_folder import create_part_folder

    create_part_folder(workspace, "mounting_plate")

    export_mod = _export_module()
    out_path = export_mod.export_part(workspace, "mounting_plate", format="iges")
    assert Path(out_path).is_file()
    assert out_path.suffix.lower() in (".iges", ".igs")


def test_export_without_geometry_fails_gracefully(workspace):
    from project.part_folder import create_part_folder

    create_part_folder(workspace, "empty_part")
    export_mod = _export_module()
    with pytest.raises(Exception) as exc_info:
        export_mod.export_part(workspace, "empty_part", format="step")
    msg = str(exc_info.value).lower()
    assert "geometry" in msg or "model" in msg or "first" in msg


def test_export_creates_history_entry(workspace, mounting_plate_ir_dict):
    pytest.importorskip("OCC.Core.TopoDS")
    from project.part_folder import create_part_folder
    from spec_fixtures import read_history_events
    from rpc_helpers import call_rpc

    create_part_folder(workspace, "mounting_plate")
    call_rpc("execute_intent", {"ir": mounting_plate_ir_dict})

    export_mod = _export_module()
    export_with_history = getattr(export_mod, "export_part_with_history", None)
    if export_with_history:
        export_with_history(workspace, "mounting_plate", format="step")
    else:
        export_mod.export_part(workspace, "mounting_plate", format="step")
        hist = pytest.importorskip("project.history")
        log_export = getattr(hist, "append_export_history", None)
        assert log_export is not None

    events = read_history_events(workspace, "mounting_plate")
    assert any(e.get("type") == "export" or "export" in e.get("summary", "").lower() for e in events)


def test_export_lands_in_exports_folder(workspace, mounting_plate_ir_dict):
    pytest.importorskip("OCC.Core.TopoDS")
    from rpc_helpers import call_rpc
    from project.part_folder import create_part_folder

    create_part_folder(workspace, "mounting_plate")
    call_rpc("execute_intent", {"ir": mounting_plate_ir_dict})
    export_mod = _export_module()
    out_path = export_mod.export_part(workspace, "mounting_plate", format="step")
    assert "exports" in str(out_path).replace("\\", "/")
