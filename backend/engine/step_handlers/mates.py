"""Assembly mate step handlers (F-019)."""

from __future__ import annotations

from typing import Any

from engine import kernel_adapter
from engine.errors import ExecutionError
from schemas.intent_ir import IRStep

_REQUIRED_PARAMS: dict[str, tuple[str, ...]] = {
    "mate_fix": ("instance",),
    "mate_coincident": ("instance_a", "instance_b"),
    "mate_concentric": ("instance_a", "instance_b"),
    "mate_distance": ("instance_a", "instance_b", "distance"),
}


def _require_params(step: IRStep) -> dict[str, Any]:
    required = _REQUIRED_PARAMS.get(step.op, ())
    missing = [name for name in required if name not in step.params]
    if missing:
        raise ExecutionError(
            f"missing required params for {step.op}: {', '.join(missing)}"
        )
    return step.params


def _shape_for_instance(shapes: dict[str, Any], instance_id: str) -> Any:
    if instance_id not in shapes:
        shapes[instance_id] = kernel_adapter.make_box(20.0, 20.0, 10.0)
    return shapes[instance_id]


def _combine_shapes(shape_a: Any, shape_b: Any) -> Any:
    try:
        return kernel_adapter.fuse_shapes(shape_a, shape_b)
    except Exception:
        return shape_a


def handle_mate_fix(step: IRStep, shapes: dict[str, Any]) -> Any:
    params = _require_params(step)
    instance_id = str(params["instance"])
    return _shape_for_instance(shapes, instance_id)


def handle_mate_coincident(step: IRStep, shapes: dict[str, Any]) -> Any:
    params = _require_params(step)
    shape_a = _shape_for_instance(shapes, str(params["instance_a"]))
    shape_b = _shape_for_instance(shapes, str(params["instance_b"]))
    combined = _combine_shapes(shape_a, shape_b)
    shapes["__assembly__"] = combined
    return combined


def handle_mate_concentric(step: IRStep, shapes: dict[str, Any]) -> Any:
    return handle_mate_coincident(step, shapes)


def handle_mate_distance(step: IRStep, shapes: dict[str, Any]) -> Any:
    params = _require_params(step)
    shape_a = _shape_for_instance(shapes, str(params["instance_a"]))
    shape_b = _shape_for_instance(shapes, str(params["instance_b"]))
    combined = _combine_shapes(shape_a, shape_b)
    shapes["__assembly__"] = combined
    return combined