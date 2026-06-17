"""Stub handler for MVP ops not implemented in F-004."""

from typing import Any

from engine.errors import StepNotImplementedError
from schemas.intent_ir import IRStep


def handle_stub(step: IRStep, shapes: dict[str, Any]) -> Any:
    raise StepNotImplementedError(step.op)
