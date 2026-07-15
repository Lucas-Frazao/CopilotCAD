"""
Stub Step Handler — Placeholder for Unimplemented MVP Ops (F-004)
===============================================================

WHAT THIS FILE DOES
-------------------
Some operation names are part of the MVP schema (``MVP_STEP_OPS``) but do not
have real geometry code yet. The handler registry routes those ops here.

BEHAVIOR
--------
Always raises ``StepNotImplementedError`` so the executor can return a clear
"not implemented" message instead of crashing silently.
"""

from typing import Any

from engine.errors import StepNotImplementedError
from schemas.intent_ir import IRStep


def handle_stub(step: IRStep, shapes: dict[str, Any]) -> Any:
    """Reject execution for MVP ops that lack a real handler implementation."""
    raise StepNotImplementedError(step.op)
