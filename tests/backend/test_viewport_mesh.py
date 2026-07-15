"""
test_viewport_mesh.py — Three.js viewport mesh tests (F-011)
============================================================

F-011 adds 3D viewport support. The backend tessellates OCCT shapes into
triangle meshes (vertices, normals, indices) that Three.js can render.

These tests verify get_part_mesh RPC registration, mesh payload shape, face-id
maps for picking, and that tessellation stays inside occt_bridge or mesh modules.

Beginner concepts:
  - Tessellation: converting a smooth 3D shape into flat triangles for the GPU.
  - Mesh payload: {vertices, normals, indices} arrays sent to the frontend.
  - face_ids: maps triangle groups back to OCCT faces for click-to-select.
"""

from __future__ import annotations

import importlib

import pytest

from rpc_helpers import assert_rpc_method_registered, call_rpc, assert_rpc_success

# Every valid mesh response must include these three arrays
MESH_REQUIRED_KEYS = frozenset({"vertices", "normals", "indices"})


def _require_mesh_module():
    """Import mesh.part_mesh or fail with a clear F-011 pending message."""
    try:
        return importlib.import_module("mesh.part_mesh")
    except ImportError as exc:
        pytest.fail(f"F-011 requires backend/mesh/part_mesh.py: {exc}")


def test_get_part_mesh_rpc_is_registered():
    """get_part_mesh must be registered as a JSON-RPC method."""
    assert_rpc_method_registered("get_part_mesh", {"part_id": "mounting_plate"})


def test_mesh_payload_shape():
    """
    After executing the golden plate IR, build_part_mesh_payload must return
    vertices, normals, and indices with consistent lengths.
    """
    mesh_mod = _require_mesh_module()
    assert hasattr(mesh_mod, "build_part_mesh_payload")

    pytest.importorskip("OCC.Core.TopoDS")
    from engine.executor import execute_intent_ir
    from ir.validator import validate_intent_ir
    from test_intent_ir_validation import mounting_plate_ir

    intent = validate_intent_ir(mounting_plate_ir())
    result = execute_intent_ir(intent)
    assert result.success, result.error

    payload = mesh_mod.build_part_mesh_payload(result.final_shape)
    assert MESH_REQUIRED_KEYS.issubset(payload.keys())
    assert len(payload["vertices"]) >= 9  # At least one triangle (3 verts × 3 coords)
    assert len(payload["indices"]) >= 3
    assert len(payload["normals"]) == len(payload["vertices"])


def test_get_part_mesh_jsonrpc_returns_mesh(
    workspace_with_mounting_plate, mounting_plate_ir_dict
):
    """get_part_mesh RPC should return a mesh dict after execute_intent runs."""
    pytest.importorskip("OCC.Core.TopoDS")

    execute = call_rpc("execute_intent", {"ir": mounting_plate_ir_dict})
    assert "result" in execute or "error" in execute

    response = call_rpc(
        "get_part_mesh",
        {
            "workspace_path": str(workspace_with_mounting_plate),
            "part_id": "mounting_plate",
        },
    )
    result = assert_rpc_success(response)
    assert MESH_REQUIRED_KEYS.issubset(result.keys())


def test_mesh_payload_includes_face_id_map_for_picking():
    """
    Viewport face picking requires face_ids or face_id_map in the mesh payload.
    F-011 acceptance criteria require this for click-to-select.
    """
    mesh_mod = _require_mesh_module()
    assert hasattr(mesh_mod, "build_part_mesh_payload")

    pytest.importorskip("OCC.Core.TopoDS")
    from engine.executor import execute_intent_ir
    from ir.validator import validate_intent_ir
    from test_intent_ir_validation import mounting_plate_ir

    intent = validate_intent_ir(mounting_plate_ir())
    result = execute_intent_ir(intent)
    payload = mesh_mod.build_part_mesh_payload(result.final_shape)
    assert "face_ids" in payload or "face_id_map" in payload


def test_tessellation_lives_in_occt_bridge_or_mesh_module():
    """
    Architecture rule: OCC imports only in occt_bridge. Tessellation must live
    in occt_bridge.tessellate_shape or mesh.part_mesh.tessellate_shape.
    """
    pytest.importorskip("OCC.Core.TopoDS")
    bridge = importlib.import_module("kernel.occt_bridge")
    mesh_mod = _require_mesh_module()
    tessellate = getattr(bridge, "tessellate_shape", None) or getattr(
        mesh_mod, "tessellate_shape", None
    )
    assert tessellate is not None, "F-011 needs tessellate_shape in occt_bridge or mesh.part_mesh"
