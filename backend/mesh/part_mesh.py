"""Part mesh payload builder for viewport rendering (F-011)."""

from __future__ import annotations

from typing import Any


def build_part_mesh_payload(shape: Any) -> dict[str, list]:
    """Tessellate a TopoDS shape into vertices, normals, indices, and face_ids."""
    if shape is None:
        return {"vertices": [], "normals": [], "indices": [], "face_ids": []}
    from kernel.occt_bridge import tessellate_shape

    return tessellate_shape(shape)