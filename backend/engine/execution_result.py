"""Execution result types for Intent IR step runs (F-004)."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExecutionResult:
    success: bool
    step_ids: list[str] = field(default_factory=list)
    final_step_id: str | None = None
    error: str | None = None
    shapes_by_step_id: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "step_ids": self.step_ids,
            "final_step_id": self.final_step_id,
            "error": self.error,
        }
