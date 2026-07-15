"""
Assembly Mesh Builder — Multi-Instance Viewport (F-020)
=======================================================

WHAT THIS FILE DOES
-------------------
Builds one mesh payload per assembly instance for the 3D viewport. Each instance
includes its own transform matrix (4×4 column-major) for positioning.

FALLBACK BEHAVIOR
-----------------
- If assembly YAML is missing, scans parts/ folder for up to MAX_ASSEMBLY_INSTANCES
- Missing geometry → 10 mm placeholder box from occt_bridge
- Multiple instances get slight X-offset so stacked placeholders remain visible

OUTPUT SHAPE
------------
{"meshes": [{instance_id, part_id, vertices, normals, indices, face_ids, transform}, ...]}
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mesh.part_mesh import build_part_mesh_payload
from project.assembly_folder import read_assembly
from project.geometry_cache import load_part_geometry

MAX_ASSEMBLY_INSTANCES = 5

# 4×4 identity matrix (column-major) — no rotation or translation
_IDENTITY_TRANSFORM = [
    1.0,
    0.0,
    0.0,
    0.0,
    0.0,
    1.0,
    0.0,
    0.0,
    0.0,
    0.0,
    1.0,
    0.0,
    0.0,
    0.0,
    0.0,
    1.0,
]


def _placeholder_shape():
    from kernel.occt_bridge import make_box

    return make_box(10.0, 10.0, 10.0)


def build_assembly_mesh_payload(workspace: Path, assembly_id: str) -> dict[str, list[dict[str, Any]]]:
    """Build per-instance mesh payloads for an assembly."""
    try:
        assembly = read_assembly(workspace, assembly_id)
        instances = assembly.get("instances", [])
    except Exception:
        instances = []

    # Dev fallback: treat each part folder as a pseudo-instance
    if not instances:
        parts_dir = workspace / "parts"
        if parts_dir.is_dir():
            for index, part_dir in enumerate(sorted(parts_dir.iterdir())[:MAX_ASSEMBLY_INSTANCES]):
                if part_dir.is_dir():
                    instances.append(
                        {
                            "instance_id": f"inst_{part_dir.name}",
                            "part_id": part_dir.name,
                        }
                    )

    instances = instances[:MAX_ASSEMBLY_INSTANCES]

    meshes: list[dict[str, Any]] = []
    for index, instance in enumerate(instances):
        instance_id = instance["instance_id"]
        part_id = instance["part_id"]
        shape = load_part_geometry(workspace, part_id)
        if shape is None:
            shape = _placeholder_shape()

        mesh_data = build_part_mesh_payload(shape)
        meshes.append(
            {
                "instance_id": instance_id,
                "part_id": part_id,
                "vertices": mesh_data["vertices"],
                "normals": mesh_data["normals"],
                "indices": mesh_data["indices"],
                "face_ids": mesh_data.get("face_ids", []),
                "transform": _IDENTITY_TRANSFORM,
            }
        )
        # Stagger instances along +X when previewing multiple parts
        if len(meshes) > 1 and shape is not None:
            offset = index * 15.0
            meshes[-1]["transform"] = [
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
                0.0,
                offset,
                0.0,
                0.0,
                1.0,
            ]

    return {"meshes": meshes}
