# =============================================================================
# Problem Objects — Problems Engine Schema (Feature F-006)
# =============================================================================
#
# WHAT THIS FILE DEFINES
# ----------------------
# After executing Intent IR, the Problems engine scans the result and emits
# Problem records: missing inputs, unresolved assumptions, geometry failures,
# mate errors, etc. The frontend shows these in the Problems panel.
#
# Each Problem has a type, severity, message, and optional suggested_next_steps.
# =============================================================================

from typing import Literal

# BaseModel — validated problem dicts
# ConfigDict — strict, no extra fields
# Field — default empty list for suggestions
from pydantic import BaseModel, ConfigDict, Field

# Machine-readable problem categories for filtering and icons
ProblemType = Literal[
    "missing_required_input",
    "unresolved_assumption",
    "geometry_generation_failure",
    "interface_conflict",
    "invalid_mate",
    "manufacturing_rule_warning",
    "traceability_gap",
]

# How urgently the user should address this problem
ProblemSeverity = Literal["warning", "error", "blocking"]


class Problem(BaseModel):
    """
    One issue surfaced to the user after compile or execute.

    part_id / step_id are optional anchors for jumping to context in the UI.
    """

    model_config = ConfigDict(extra="forbid", strict=True)

    id: str
    type: ProblemType
    severity: ProblemSeverity
    message: str
    part_id: str | None = None
    step_id: str | None = None
    suggested_next_steps: list[str] = Field(default_factory=list)
