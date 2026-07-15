"""
Geometry Cache — STEP Persist + Session Memory (F-012)
========================================================

WHAT THIS FILE DOES
-------------------
Saves and loads OCCT shapes for each part:

  Disk:   parts/<part_id>/geometry.step
  Memory: _SESSION_SHAPES dict (for tests / RPC without workspace path)

WHY TWO LAYERS?
---------------
Executor may run geometry in memory first; session cache lets mesh/export work
before the user picks a workspace folder.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

GEOMETRY_FILENAME = "geometry.step"

# In-process fallback when execute runs without a workspace path (tests / RPC).
_SESSION_SHAPES: dict[str, Any] = {}


def geometry_path(workspace: Path, part_id: str) -> Path:
    return workspace / "parts" / part_id / GEOMETRY_FILENAME


def save_part_geometry(workspace: Path, part_id: str, shape: Any) -> Path:
    """Write shape to parts/<id>/geometry.step and update session cache."""
    from kernel.occt_bridge import export_step

    path = geometry_path(workspace, part_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    export_step(shape, path)
    _SESSION_SHAPES[part_id] = shape
    return path


def load_part_geometry(workspace: Path, part_id: str) -> Any | None:
    """Load shape from disk if present, else from session cache."""
    path = geometry_path(workspace, part_id)
    if path.is_file():
        from kernel.occt_bridge import read_step

        shape = read_step(path)
        _SESSION_SHAPES[part_id] = shape
        return shape
    return _SESSION_SHAPES.get(part_id)


def cache_session_shape(part_id: str, shape: Any) -> None:
    """Remember the latest shape for a part when no workspace write occurred."""
    _SESSION_SHAPES[part_id] = shape


def clear_session_shapes() -> None:
    """Reset session cache — used between tests."""
    _SESSION_SHAPES.clear()
