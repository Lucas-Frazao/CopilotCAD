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
