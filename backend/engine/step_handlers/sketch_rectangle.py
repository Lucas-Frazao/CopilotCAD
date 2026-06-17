"""sketch_rectangle step handler (F-004)."""

from typing import Any

from engine import kernel_adapter
from engine.errors import ExecutionError
from schemas.intent_ir import IRStep


def _require_param(params: dict[str, Any], name: str) -> Any:
    if name not in params:
        raise ExecutionError(f"missing required param '{name}' for sketch_rectangle")
    return params[name]


def handle_sketch_rectangle(step: IRStep, shapes: dict[str, Any]) -> Any:
    if step.from_step is not None:
        raise ExecutionError("sketch_rectangle must not have a from dependency")

    params = step.params
    return kernel_adapter.sketch_rectangle(
        float(_require_param(params, "length")),
        float(_require_param(params, "width")),
        str(_require_param(params, "plane")),
        str(_require_param(params, "mode")),
    )
