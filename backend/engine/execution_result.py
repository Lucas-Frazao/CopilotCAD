"""
============================================================================
FILE: execution_result.py — Result object after running CAD steps (F-004)
============================================================================

When the backend "executes" a sequence of CAD steps (sketch, extrude, etc.),
it needs a structured way to report what happened: success or failure, which
steps ran, any error message, and references to 3D shapes produced.

This module defines ExecutionResult, a simple data container (dataclass) that
the executor returns to callers (JSON-RPC handlers, tests, etc.).

Feature F-004 introduced step execution; this type is the contract for outcomes.
============================================================================
"""

# dataclass: a decorator that auto-generates __init__, __repr__, etc. for
# classes that mostly hold data fields.
from dataclasses import dataclass, field

# Any means "any Python type" — used here for OCCT shape objects we do not
# type strictly in this layer.
from typing import Any


@dataclass
class ExecutionResult:
    """
    Outcome of running one or more Intent IR steps through the step engine.

    Attributes:
        success: True if all requested steps completed without error.
        step_ids: Ordered list of step identifiers that were executed.
        final_step_id: The last step in the chain (often the "current" geometry).
        error: Human-readable error string when success is False; otherwise None.
        shapes_by_step_id: Maps each step id to its kernel shape object (in-memory only).
    """

    # Required field: did the run succeed?
    success: bool

    # List of step IDs executed, in order. default_factory=list means "new empty
    # list per instance" — never share one list across all ExecutionResult objects.
    step_ids: list[str] = field(default_factory=list)

    # Which step is considered "final" for geometry lookup; optional.
    final_step_id: str | None = None

    # Error message when success is False.
    error: str | None = None

    # Internal map of step id -> shape handle. Not always serialized to JSON.
    shapes_by_step_id: dict[str, Any] = field(default_factory=dict)

    @property
    def final_shape(self) -> Any:
        """
        Convenience accessor: return the shape for final_step_id, or None if
        there is no final step or that step has no shape stored.
        """
        # No final step means no shape to return.
        if self.final_step_id is None:
            return None
        # .get() returns None if the key is missing instead of raising KeyError.
        return self.shapes_by_step_id.get(self.final_step_id)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to a JSON-friendly dictionary for RPC responses.

        Note: shapes_by_step_id is omitted — OCCT shapes are not serializable.
        """
        return {
            "success": self.success,
            "step_ids": self.step_ids,
            "final_step_id": self.final_step_id,
            "error": self.error,
        }
