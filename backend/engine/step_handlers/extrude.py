"""
Extrude Handler — Profile → Solid Step (F-004)
==============================================

WHAT THIS FILE DOES
-------------------
Runs the ``extrude`` IR step: takes a 2D profile from a prior step and sweeps
it into a 3D solid along an axis.

PARAMS
------
- distance — extrusion depth in mm
- direction — e.g. "+Z"
- mode — e.g. "add"

DEPENDENCIES
------------
Requires ``step.from_step`` pointing at a sketch (or other face-producing step).
"""

from typing import Any

from engine import kernel_adapter
from engine.errors import ExecutionError
from schemas.intent_ir import IRStep


def _require_param(params: dict[str, Any], name: str) -> Any:
    if name not in params:
        raise ExecutionError(f"missing required param '{name}' for extrude")
    return params[name]


def _require_input_shape(step: IRStep, shapes: dict[str, Any]) -> Any:
    """Look up the parent step's geometry output in the shapes dict."""
    if step.from_step is None:
        raise ExecutionError(f"step '{step.id}' requires a from dependency")
    if step.from_step not in shapes:
        raise ExecutionError(
            f"step '{step.id}' references missing shape from '{step.from_step}'"
        )
    return shapes[step.from_step]


def handle_extrude(step: IRStep, shapes: dict[str, Any]) -> Any:
    """Execute extrude: pull profile from shapes, forward params to kernel."""
    profile = _require_input_shape(step, shapes)
    params = step.params
    return kernel_adapter.extrude(
        profile,
        float(_require_param(params, "distance")),
        str(_require_param(params, "direction")),
        str(_require_param(params, "mode")),
    )
