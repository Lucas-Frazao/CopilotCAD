"""
Kernel Adapter — Safe Gateway to OCCT (F-004)
==============================================

WHAT THIS FILE DOES
-------------------
Provides simple Python functions (sketch_rectangle, extrude, etc.) that the
step handlers call. Each function forwards work to ``kernel.occt_bridge``.

WHY THIS LAYER EXISTS
---------------------
Architecture rule: only ``occt_bridge.py`` may import pythonOCC directly.
Step handlers talk to *this* adapter instead, keeping OCCT isolated.

IMPORT PATTERN
--------------
Functions import from ``kernel.occt_bridge`` *inside* the function body (lazy
import). That way the rest of the backend can load even when pythonOCC is not
installed (tests on unsupported platforms skip OCCT).
"""

from typing import Any


def sketch_rectangle(length: float, width: float, plane: str, mode: str) -> Any:
    """Create a 2D rectangular profile on the given plane."""
    from kernel.occt_bridge import sketch_rectangle as bridge_sketch_rectangle

    return bridge_sketch_rectangle(length, width, plane, mode)


def extrude(profile: Any, distance: float, direction: str, mode: str) -> Any:
    """Sweep a 2D profile into a 3D solid along direction."""
    from kernel.occt_bridge import extrude as bridge_extrude

    return bridge_extrude(profile, distance, direction, mode)


def hole_pattern_corners(solid: Any, diameter: float, offset: float) -> Any:
    """Cut four corner holes into a rectangular plate solid."""
    from kernel.occt_bridge import hole_pattern_corners as bridge_hole_pattern_corners

    return bridge_hole_pattern_corners(solid, diameter, offset)


def make_box(length: float, width: float, height: float) -> Any:
    """Build a simple box — used as a placeholder when assembly geometry is missing."""
    from kernel.occt_bridge import make_box as bridge_make_box

    return bridge_make_box(length, width, height)


def fuse_shapes(shape_a: Any, shape_b: Any) -> Any:
    """Boolean-union two solids (mate handlers combine instance shapes)."""
    from kernel.occt_bridge import fuse_shapes as bridge_fuse_shapes

    return bridge_fuse_shapes(shape_a, shape_b)


def make_box_at(dx: float, dy: float, dz: float, xmin: float, ymin: float, zmin: float) -> Any:
    """Build a box of size (dx, dy, dz) with min-corner at (xmin, ymin, zmin)."""
    from kernel.occt_bridge import make_box_at as bridge_make_box_at

    return bridge_make_box_at(dx, dy, dz, xmin, ymin, zmin)


def make_cylinder(
    radius: float,
    height: float,
    x: float,
    y: float,
    z: float,
    direction: str = "+Z",
) -> Any:
    """Build a cylinder with base center (x, y, z)."""
    from kernel.occt_bridge import make_cylinder as bridge_make_cylinder

    return bridge_make_cylinder(radius, height, x, y, z, direction)


def sketch_polygon(points: list[tuple[float, float]]) -> Any:
    """Build a planar polygonal face on Z=0."""
    from kernel.occt_bridge import sketch_polygon as bridge_sketch_polygon

    return bridge_sketch_polygon(points)


def cut_shape(solid: Any, tool: Any) -> Any:
    """Boolean-subtract tool from solid."""
    from kernel.occt_bridge import cut_shape as bridge_cut_shape

    return bridge_cut_shape(solid, tool)


def translate_shape(shape: Any, dx: float, dy: float, dz: float) -> Any:
    """Translate a shape by (dx, dy, dz)."""
    from kernel.occt_bridge import translate_shape as bridge_translate_shape

    return bridge_translate_shape(shape, dx, dy, dz)


def shape_bbox(shape: Any) -> tuple[float, float, float, float, float, float]:
    """Return (xmin, ymin, zmin, xmax, ymax, zmax)."""
    from kernel.occt_bridge import shape_bbox as bridge_shape_bbox

    return bridge_shape_bbox(shape)


def shape_volume(shape: Any) -> float:
    """Return absolute solid volume in cubic model units."""
    from kernel.occt_bridge import shape_volume as bridge_shape_volume

    return bridge_shape_volume(shape)


def count_subshapes(shape: Any, kind: str) -> int:
    """Count SOLID, SHELL, or FACE children."""
    from kernel.occt_bridge import count_subshapes as bridge_count_subshapes

    return bridge_count_subshapes(shape, kind)


def is_valid_manifold(shape: Any) -> bool:
    """True when OCCT considers the B-rep valid / manifold."""
    from kernel.occt_bridge import is_valid_manifold as bridge_is_valid_manifold

    return bridge_is_valid_manifold(shape)


def classify_point(shape: Any, x: float, y: float, z: float) -> str:
    """Classify a point as 'in', 'out', or 'on'."""
    from kernel.occt_bridge import classify_point as bridge_classify_point

    return bridge_classify_point(shape, x, y, z)


def export_stl(shape: Any, path: Any) -> None:
    """Write a binary STL (dogfood only)."""
    from kernel.occt_bridge import export_stl as bridge_export_stl

    bridge_export_stl(shape, path)


def export_step(shape: Any, path: Any) -> None:
    """Write a STEP file via the OCCT bridge."""
    from kernel.occt_bridge import export_step as bridge_export_step

    bridge_export_step(shape, path)


def export_iges(shape: Any, path: Any) -> None:
    """Write an IGES file via the OCCT bridge."""
    from kernel.occt_bridge import export_iges as bridge_export_iges

    bridge_export_iges(shape, path)
