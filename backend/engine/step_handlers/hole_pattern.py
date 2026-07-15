"""
Hole Pattern Corners Handler — Four Corner Holes (F-004)
========================================================

WHAT THIS FILE DOES
-------------------
Runs the ``hole_pattern_corners`` IR step: cuts four cylindrical holes near the
corners of a rectangular plate solid.

PARAMS
------
- diameter — hole diameter in mm
- offset — inset from each corner edge in mm

DEPENDENCIES
------------
Requires ``step.from_step`` pointing at an extruded solid (typically a plate).
"""

from typing import Any

from engine import kernel_adapter
from engine.errors import ExecutionError
from schemas.intent_ir import IRStep


def _require_param(params: dict[str, Any], name: str) -> Any:
    if name not in params:
        raise ExecutionError(f"missing required param '{name}' for hole_pattern_corners")
    return params[name]


def _require_input_shape(step: IRStep, shapes: dict[str, Any]) -> Any:
    if step.from_step is None:
        raise ExecutionError(f"step '{step.id}' requires a from dependency")
    if step.from_step not in shapes:
        raise ExecutionError(
            f"step '{step.id}' references missing shape from '{step.from_step}'"
        )
    return shapes[step.from_step]


def handle_hole_pattern_corners(step: IRStep, shapes: dict[str, Any]) -> Any:
    """Execute hole_pattern_corners on the input solid."""
    solid = _require_input_shape(step, shapes)
    params = step.params
    return kernel_adapter.hole_pattern_corners(
        solid,
        float(_require_param(params, "diameter")),
        float(_require_param(params, "offset")),
    )
