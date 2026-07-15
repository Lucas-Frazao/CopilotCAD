"""
Handler Registry — Step Op → Handler Lookup (F-004)
====================================================

WHAT THIS FILE DOES
-------------------
Intent IR describes CAD work as a list of "steps". Each step has an ``op`` field
(operation name) such as ``sketch_rectangle`` or ``extrude``.

This module is the lookup table: given an ``op`` string, return the Python
function that knows how to run that step.

HOW IT FITS IN THE PIPELINE
---------------------------
  Chat → LLM → Intent IR → executor.py loops steps → get_handler(op) → handler

LEARNING NOTES
--------------
- A *handler* receives the step definition plus a dict of shapes built so far.
- Fully implemented ops live in ``_IMPLEMENTED``.
- MVP ops that are not yet coded fall back to ``handle_stub`` (raises not-implemented).
- Unknown ops outside the MVP set raise ``ExecutionError``.
"""

# Callable: type hint for "a function you can call"
from collections.abc import Callable
# Any: geometry objects from OCCT have no stable Python type in our stubs
from typing import Any

from engine.errors import ExecutionError
# One import per step handler — each lives in engine/step_handlers/
from engine.step_handlers.extrude import handle_extrude
from engine.step_handlers.hole_pattern import handle_hole_pattern_corners
from engine.step_handlers.mates import (
    handle_mate_coincident,
    handle_mate_concentric,
    handle_mate_distance,
    handle_mate_fix,
)
from engine.step_handlers.sketch_rectangle import handle_sketch_rectangle
from engine.step_handlers.stub import handle_stub
# IRStep: Pydantic model for one step; MVP_STEP_OPS: frozenset of allowed op names
from schemas.intent_ir import IRStep, MVP_STEP_OPS

# StepHandler = "function(step, shapes) -> geometry output"
StepHandler = Callable[[IRStep, dict[str, Any]], Any]

# Maps op name → handler function. Only ops listed here have real implementations.
_IMPLEMENTED: dict[str, StepHandler] = {
    "sketch_rectangle": handle_sketch_rectangle,
    "extrude": handle_extrude,
    "hole_pattern_corners": handle_hole_pattern_corners,
    "mate_fix": handle_mate_fix,
    "mate_coincident": handle_mate_coincident,
    "mate_concentric": handle_mate_concentric,
    "mate_distance": handle_mate_distance,
}


def get_handler(op: str) -> StepHandler:
    """Return the handler callable for a step operation name."""
    if op in _IMPLEMENTED:
        return _IMPLEMENTED[op]
    # MVP op but no real handler yet — stub will raise StepNotImplementedError
    if op in MVP_STEP_OPS:
        return handle_stub
    raise ExecutionError(f"unknown step op: {op}")


def registered_ops() -> frozenset[str]:
    """Expose the full MVP op set (implemented + stubbed)."""
    return MVP_STEP_OPS
