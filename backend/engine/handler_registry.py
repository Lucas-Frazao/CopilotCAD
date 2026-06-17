"""Maps IR step ops to handler callables (F-004)."""

from collections.abc import Callable
from typing import Any

from engine.errors import ExecutionError
from engine.step_handlers.extrude import handle_extrude
from engine.step_handlers.hole_pattern import handle_hole_pattern_corners
from engine.step_handlers.sketch_rectangle import handle_sketch_rectangle
from engine.step_handlers.stub import handle_stub
from schemas.intent_ir import IRStep, MVP_STEP_OPS

StepHandler = Callable[[IRStep, dict[str, Any]], Any]

_IMPLEMENTED: dict[str, StepHandler] = {
    "sketch_rectangle": handle_sketch_rectangle,
    "extrude": handle_extrude,
    "hole_pattern_corners": handle_hole_pattern_corners,
}


def get_handler(op: str) -> StepHandler:
    if op in _IMPLEMENTED:
        return _IMPLEMENTED[op]
    if op in MVP_STEP_OPS:
        return handle_stub
    raise ExecutionError(f"unknown step op: {op}")


def registered_ops() -> frozenset[str]:
    return MVP_STEP_OPS
