"""Pydantic models for Intent IR (slim schema)."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# MVP step catalog — valid op types for IR steps.
MVP_STEP_OPS: frozenset[str] = frozenset(
    {
        "sketch_rectangle",
        "sketch_circle",
        "extrude",
        "cut_extrude",
        "revolve",
        "hole_simple",
        "hole_pattern_corners",
        "fillet",
        "chamfer",
        "pattern_linear",
        "pattern_circular",
        "mirror",
        "shell",
        "offset_face",
        "create_plane",
        "create_axis",
        "create_point",
        "mate_fix",
        "mate_coincident",
        "mate_concentric",
        "mate_distance",
    }
)

IntentType = Literal[
    "part_create",
    "part_edit",
    "assembly_create",
    "doc_scaffold",
    "export",
    "release",
]

AssumptionScope = Literal["part", "assembly", "project"]
AssumptionSource = Literal["user", "ai", "spec"]
AssumptionImportance = Literal["low", "medium", "high"]
AssumptionStatus = Literal["proposed", "confirmed", "rejected"]

QuestionStatus = Literal["open", "answered", "dismissed"]


class IRTarget(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    part_id: str | None = None
    assembly_id: str | None = None
    doc_path: str | None = None


class IRContext(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    active_part_id: str | None = None
    selection: list[str] = Field(default_factory=list)
    workspace_path: str | None = None


class IRQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    id: str
    text: str
    blocking: bool = False
    status: QuestionStatus = "open"
    answer: str | None = None


class IRAssumption(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    id: str
    text: str
    scope: AssumptionScope = "part"
    source: AssumptionSource = "ai"
    importance: AssumptionImportance = "medium"
    status: AssumptionStatus = "proposed"


class IRConstraints(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    dimensions: dict[str, Any] = Field(default_factory=dict)
    material: str | None = None
    process: str | None = None
    tolerance: dict[str, Any] = Field(default_factory=dict)
    interfaces: list[str] = Field(default_factory=list)


class IRStep(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, populate_by_name=True)

    id: str
    op: str
    params: dict[str, Any] = Field(default_factory=dict)
    from_step: str | None = Field(default=None, alias="from")


class IRLinks(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    spec_refs: list[str] = Field(default_factory=list)
    requirement_refs: list[str] = Field(default_factory=list)
    architecture_refs: list[str] = Field(default_factory=list)


class IntentIR(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    type: IntentType
    prompt: str
    summary: str
    target: IRTarget
    context: IRContext = Field(default_factory=IRContext)
    questions: list[IRQuestion] = Field(default_factory=list)
    assumptions: list[IRAssumption] = Field(default_factory=list)
    constraints: IRConstraints = Field(default_factory=IRConstraints)
    steps: list[IRStep] = Field(default_factory=list)
    links: IRLinks = Field(default_factory=IRLinks)
