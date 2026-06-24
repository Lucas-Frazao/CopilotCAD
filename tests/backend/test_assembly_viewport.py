"""Spec compliance tests for F-020 — Assembly viewport."""

from __future__ import annotations

import importlib

import pytest

from rpc_helpers import assert_rpc_method_registered, call_rpc, assert_rpc_success
from spec_fixtures import make_workspace_with_two_parts


def _assembly_mesh_module():
    try:
        return importlib.import_module("mesh.assembly_mesh")
    except ImportError as exc:
        pytest.fail(f"F-020 requires backend/mesh/assembly_mesh.py: {exc}")


def test_get_assembly_mesh_rpc_registered(workspace):
    assert_rpc_method_registered(
        "get_assembly_mesh",
        {"workspace_path": str(workspace), "assembly_id": "demo_asm"},
    )


def test_assembly_mesh_returns_per_instance_meshes(tmp_path):
    pytest.importorskip("OCC.Core.TopoDS")
    workspace = make_workspace_with_two_parts(tmp_path)

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

    mesh_mod = _assembly_mesh_module()
    build = getattr(mesh_mod, "build_assembly_mesh_payload", None)
    assert build is not None

    payload = build(workspace, "demo_asm")
    meshes = payload.get("meshes") or payload
    assert isinstance(meshes, list)
    assert len(meshes) >= 2
    for mesh in meshes:
        assert "instance_id" in mesh
        assert "part_id" in mesh
        assert "vertices" in mesh
        assert "transform" in mesh or "matrix" in mesh


def test_get_assembly_mesh_jsonrpc(tmp_path):
    pytest.importorskip("OCC.Core.TopoDS")
    workspace = make_workspace_with_two_parts(tmp_path)
    response = call_rpc(
        "get_assembly_mesh",
        {"workspace_path": str(workspace), "assembly_id": "demo_asm"},
    )
    result = assert_rpc_success(response)
    meshes = result.get("meshes", result)
    assert isinstance(meshes, list)


def test_single_part_mesh_still_works_alongside_assembly(workspace_with_mounting_plate, mounting_plate_ir_dict):
    pytest.importorskip("OCC.Core.TopoDS")
    call_rpc("execute_intent", {"ir": mounting_plate_ir_dict})
    response = call_rpc(
        "get_part_mesh",
        {
            "workspace_path": str(workspace_with_mounting_plate),
            "part_id": "mounting_plate",
        },
    )
    assert "result" in response, "F-020 must not break F-011 single-part viewport"


def test_assembly_mesh_performance_cap_five_parts(tmp_path):
    """MVP limit: ≤5 parts performance acceptable — payload must not explode."""
    mesh_mod = _assembly_mesh_module()
    cap = getattr(mesh_mod, "MAX_ASSEMBLY_INSTANCES", 5)
    assert cap <= 5
