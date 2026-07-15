"""
Sketch Rectangle Handler — 2D Profile Step (F-004)
==================================================

WHAT THIS FILE DOES
-------------------
Runs the ``sketch_rectangle`` IR step: creates a flat rectangular face that
later steps (like ``extrude``) can turn into a solid.

PARAMS (from step.params)
-------------------------
- length, width — mm
- plane — e.g. "XY"
- mode — e.g. "center" (rectangle centered on origin)

DEPENDENCIES
------------
This step must NOT have a ``from`` field — it starts a new geometry chain.
"""

from typing import Any

from engine import kernel_adapter  # Thin wrapper over occt_bridge
from engine.errors import ExecutionError
from schemas.intent_ir import IRStep


def _require_param(params: dict[str, Any], name: str) -> Any:
    """Raise a clear error if a required param key is missing."""
    if name not in params:
        raise ExecutionError(f"missing required param '{name}' for sketch_rectangle")
    return params[name]


def handle_sketch_rectangle(step: IRStep, shapes: dict[str, Any]) -> Any:
    """Execute sketch_rectangle: validate inputs, call kernel, return face shape."""
    if step.from_step is not None:
        raise ExecutionError("sketch_rectangle must not have a from dependency")

    params = step.params
    return kernel_adapter.sketch_rectangle(
        float(_require_param(params, "length")),
        float(_require_param(params, "width")),
        str(_require_param(params, "plane")),
        str(_require_param(params, "mode")),
    )
