"""
Assembly Mate Handlers — Combine Instance Geometry (F-019)
========================================================

WHAT THIS FILE DOES
-------------------
Handles mate_* IR steps for assemblies. Mates describe how part instances
connect. MVP implementation uses placeholder boxes and boolean fuse — not full
constraint solving yet.

SUPPORTED OPS
-------------
- mate_fix — anchor one instance
- mate_coincident / mate_concentric — align two instances (same code path)
- mate_distance — two instances at a stated distance (fuse for preview)

KEY CONCEPT
-----------
``shapes`` is keyed by *instance_id* (not step id) for preloaded assembly parts.
Combined result is also stored under ``__assembly__`` for the viewport.
"""

from __future__ import annotations

from typing import Any

from engine import kernel_adapter
from engine.errors import ExecutionError
from schemas.intent_ir import IRStep

# Each mate op requires a specific set of param keys
_REQUIRED_PARAMS: dict[str, tuple[str, ...]] = {
    "mate_fix": ("instance",),
    "mate_coincident": ("instance_a", "instance_b"),
    "mate_concentric": ("instance_a", "instance_b"),
    "mate_distance": ("instance_a", "instance_b", "distance"),
}


def _require_params(step: IRStep) -> dict[str, Any]:
    """Validate that all required params for this mate op are present."""
    required = _REQUIRED_PARAMS.get(step.op, ())
    missing = [name for name in required if name not in step.params]
    if missing:
        raise ExecutionError(
            f"missing required params for {step.op}: {', '.join(missing)}"
        )
    return step.params


def _shape_for_instance(shapes: dict[str, Any], instance_id: str) -> Any:
    """Return geometry for an instance; create a placeholder box if missing."""
    if instance_id not in shapes:
        shapes[instance_id] = kernel_adapter.make_box(20.0, 20.0, 10.0)
    return shapes[instance_id]


def _combine_shapes(shape_a: Any, shape_b: Any) -> Any:
    """Fuse two shapes; on failure return shape_a so execution can continue."""
    try:
        return kernel_adapter.fuse_shapes(shape_a, shape_b)
    except Exception:
        return shape_a


def handle_mate_fix(step: IRStep, shapes: dict[str, Any]) -> Any:
    """Fix (anchor) a single instance — returns its shape unchanged."""
    params = _require_params(step)
    instance_id = str(params["instance"])
    return _shape_for_instance(shapes, instance_id)


def handle_mate_coincident(step: IRStep, shapes: dict[str, Any]) -> Any:
    """Coincident mate: fuse two instance shapes for assembly preview."""
    params = _require_params(step)
    shape_a = _shape_for_instance(shapes, str(params["instance_a"]))
    shape_b = _shape_for_instance(shapes, str(params["instance_b"]))
    combined = _combine_shapes(shape_a, shape_b)
    shapes["__assembly__"] = combined
    return combined


def handle_mate_concentric(step: IRStep, shapes: dict[str, Any]) -> Any:
    """Concentric uses the same MVP preview path as coincident."""
    return handle_mate_coincident(step, shapes)


def handle_mate_distance(step: IRStep, shapes: dict[str, Any]) -> Any:
    """Distance mate: fuse instances (distance param reserved for future solver)."""
    params = _require_params(step)
    shape_a = _shape_for_instance(shapes, str(params["instance_a"]))
    shape_b = _shape_for_instance(shapes, str(params["instance_b"]))
    combined = _combine_shapes(shape_a, shape_b)
    shapes["__assembly__"] = combined
    return combined
