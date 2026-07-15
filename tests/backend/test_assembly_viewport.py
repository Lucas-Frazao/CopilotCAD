"""
test_assembly_viewport.py — Assembly viewport spec compliance tests (F-020)
===========================================================================

F-020 extends the 3D viewport to show multiple part instances in an assembly,
each with its own mesh and transform matrix. These tests verify get_assembly_mesh
RPC, per-instance mesh payloads, and that single-part mesh (F-011) still works.

Beginner concepts:
  - Assembly mesh: list of {instance_id, part_id, vertices, transform} dicts.
  - Transform/matrix: 4×4 matrix placing each instance in assembly space.
  - MAX_ASSEMBLY_INSTANCES: soft cap on instances for MVP performance.
"""

from __future__ import annotations

import importlib

import pytest

from rpc_helpers import assert_rpc_method_registered, call_rpc, assert_rpc_success
from spec_fixtures import make_workspace_with_two_parts


def _assembly_mesh_module():
    """Import mesh.assembly_mesh or fail with a clear F-020 pending message."""
    try:
        return importlib.import_module("mesh.assembly_mesh")
    except ImportError as exc:
        pytest.fail(f"F-020 requires backend/mesh/assembly_mesh.py: {exc}")


def test_get_assembly_mesh_rpc_registered(workspace):
    """get_assembly_mesh must be registered as a JSON-RPC method."""
    assert_rpc_method_registered(
        "get_assembly_mesh",
        {"workspace_path": str(workspace), "assembly_id": "demo_asm"},
    )


def test_assembly_mesh_returns_per_instance_meshes(tmp_path):
    """
    build_assembly_mesh_payload must return one mesh entry per assembly instance,
    each with instance_id, part_id, vertices, and a transform/matrix.
    """
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
    """get_assembly_mesh RPC should return a list of instance meshes."""
    pytest.importorskip("OCC.Core.TopoDS")
    workspace = make_workspace_with_two_parts(tmp_path)
    response = call_rpc(
        "get_assembly_mesh",
        {"workspace_path": str(workspace), "assembly_id": "demo_asm"},
    )
    result = assert_rpc_success(response)
    meshes = result.get("meshes", result)
    assert isinstance(meshes, list)


def test_single_part_mesh_still_works_alongside_assembly(
    workspace_with_mounting_plate, mounting_plate_ir_dict
):
    """
    F-020 must not break F-011: get_part_mesh must still work for single parts.
    """
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
    """
    MVP limit: ≤5 parts per assembly for acceptable performance.
    MAX_ASSEMBLY_INSTANCES must be ≤ 5.
    """
    mesh_mod = _assembly_mesh_module()
    cap = getattr(mesh_mod, "MAX_ASSEMBLY_INSTANCES", 5)
    assert cap <= 5
