"""Problem objects surfaced by the Problems engine (F-006)."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ProblemType = Literal[
    "missing_required_input",
    "unresolved_assumption",
    "geometry_generation_failure",
    "interface_conflict",
    "invalid_mate",
    "manufacturing_rule_warning",
    "traceability_gap",
]

ProblemSeverity = Literal["warning", "error", "blocking"]


class Problem(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    id: str
    type: ProblemType
    severity: ProblemSeverity
    message: str
    part_id: str | None = None
    step_id: str | None = None
    suggested_next_steps: list[str] = Field(default_factory=list)
