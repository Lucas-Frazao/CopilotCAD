"""Execution errors for the step engine (F-004)."""


class ExecutionError(Exception):
    """Raised when step sequencing or inputs are invalid."""


class StepNotImplementedError(Exception):
    """Raised when a step op is registered but not implemented in F-004."""

    def __init__(self, op: str) -> None:
        self.op = op
        super().__init__(f"step op not implemented: {op}")
