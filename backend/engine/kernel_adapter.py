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
