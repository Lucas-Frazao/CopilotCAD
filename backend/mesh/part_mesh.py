"""
Part Mesh Builder — 3D Viewport Triangles (F-011)
=================================================

WHAT THIS FILE DOES
-------------------
Converts an OCCT TopoDS shape into a JSON-friendly mesh payload the Electron
viewport can render: vertices, normals, triangle indices, and per-triangle face ids.

DATA FLOW
---------
  OCCT shape → occt_bridge.tessellate_shape → dict → JSON-RPC → Three.js mesh

EMPTY SHAPE
-----------
Returns empty lists when shape is None so the UI can clear the viewport safely.
"""

from __future__ import annotations

from typing import Any


def build_part_mesh_payload(shape: Any) -> dict[str, list]:
    """Tessellate a TopoDS shape into vertices, normals, indices, and face_ids."""
    if shape is None:
        return {"vertices": [], "normals": [], "indices": [], "face_ids": []}
    from kernel.occt_bridge import tessellate_shape

    return tessellate_shape(shape)
