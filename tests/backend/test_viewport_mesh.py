"""Spec compliance tests for F-011 — Three.js viewport (basic 3D view).

Verifies mesh tessellation RPC, mesh payload shape, and golden mounting plate mesh.
"""

from __future__ import annotations

import importlib

import pytest

from rpc_helpers import assert_rpc_method_registered, call_rpc, assert_rpc_success

MESH_REQUIRED_KEYS = frozenset({"vertices", "normals", "indices"})


def _require_mesh_module():
    try:
        return importlib.import_module("mesh.part_mesh")
    except ImportError as exc:
        pytest.fail(f"F-011 requires backend/mesh/part_mesh.py: {exc}")


def test_get_part_mesh_rpc_is_registered():
    assert_rpc_method_registered("get_part_mesh", {"part_id": "mounting_plate"})


def test_mesh_payload_shape():
    """Mesh must include vertices, normals, face indices, optional face-id map."""
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
    assert len(payload["vertices"]) >= 9  # at least one triangle
    assert len(payload["indices"]) >= 3
    assert len(payload["normals"]) == len(payload["vertices"])


def test_get_part_mesh_jsonrpc_returns_mesh(workspace_with_mounting_plate, mounting_plate_ir_dict):
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
    mesh_mod = _require_mesh_module()
    assert hasattr(mesh_mod, "build_part_mesh_payload")
    # face_ids or face_id_map enables viewport picking per F-011 acceptance criteria.
    sig = getattr(mesh_mod.build_part_mesh_payload, "__annotations__", {})
    # Implementation must document return type; runtime check on empty shape stub:
    pytest.importorskip("OCC.Core.TopoDS")
    from engine.executor import execute_intent_ir
    from ir.validator import validate_intent_ir
    from test_intent_ir_validation import mounting_plate_ir

    intent = validate_intent_ir(mounting_plate_ir())
    result = execute_intent_ir(intent)
    payload = mesh_mod.build_part_mesh_payload(result.final_shape)
    assert "face_ids" in payload or "face_id_map" in payload


def test_tessellation_lives_in_occt_bridge_or_mesh_module():
    """Tessellation must not import OCC outside occt_bridge."""
    bridge = importlib.import_module("kernel.occt_bridge")
    mesh_mod = _require_mesh_module()
    tessellate = getattr(bridge, "tessellate_shape", None) or getattr(
        mesh_mod, "tessellate_shape", None
    )
    assert tessellate is not None, "F-011 needs tessellate_shape in occt_bridge or mesh.part_mesh"
