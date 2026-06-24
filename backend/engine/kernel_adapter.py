"""Thin wrapper over pythonOCC calls (F-004)."""

from typing import Any


def sketch_rectangle(length: float, width: float, plane: str, mode: str) -> Any:
    from kernel.occt_bridge import sketch_rectangle as bridge_sketch_rectangle

    return bridge_sketch_rectangle(length, width, plane, mode)


def extrude(profile: Any, distance: float, direction: str, mode: str) -> Any:
    from kernel.occt_bridge import extrude as bridge_extrude

    return bridge_extrude(profile, distance, direction, mode)


def hole_pattern_corners(solid: Any, diameter: float, offset: float) -> Any:
    from kernel.occt_bridge import hole_pattern_corners as bridge_hole_pattern_corners

    return bridge_hole_pattern_corners(solid, diameter, offset)


def make_box(length: float, width: float, height: float) -> Any:
    from kernel.occt_bridge import make_box as bridge_make_box

    return bridge_make_box(length, width, height)


def fuse_shapes(shape_a: Any, shape_b: Any) -> Any:
    from kernel.occt_bridge import fuse_shapes as bridge_fuse_shapes

    return bridge_fuse_shapes(shape_a, shape_b)
