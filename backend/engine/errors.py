"""
============================================================================
FILE: errors.py — Exceptions for the CAD step execution engine (F-004)
============================================================================

Python uses "exceptions" to signal errors without crashing the whole program
immediately. Callers can catch specific exception types and show helpful messages.

This module defines errors raised when:
  - Step sequencing or inputs are invalid (ExecutionError)
  - A step operation is known to the registry but not implemented yet
    (StepNotImplementedError)

Feature F-004: step engine foundation.
============================================================================
"""


class ExecutionError(Exception):
    """
    Raised when step sequencing or inputs are invalid.

    Example: referencing a step id that does not exist, or circular dependencies
    in the step graph. Inherits from Exception so it can be caught like any
    Python error.
    """


class StepNotImplementedError(Exception):
    """
    Raised when a step op is registered in the handler registry but has no
    real implementation yet (stub handler).

    Stores the operation name on self.op so UIs or logs can say which op failed.
    """

    def __init__(self, op: str) -> None:
        # Remember which operation (e.g. "fillet") was requested.
        self.op = op
        # Call the base Exception constructor with a readable message string.
        super().__init__(f"step op not implemented: {op}")
