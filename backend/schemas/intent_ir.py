# =============================================================================
# Intent IR Schema — Pydantic Models (Slim MVP)
# =============================================================================
#
# WHAT THIS FILE DEFINES
# ----------------------
# Intent IR is the contract between chat, the LLM, and the CAD executor.
# A single IntentIR document describes *what* to do (part_create, export, …),
# *where* (target part/assembly), *constraints* (dimensions, material), and
# *how* (ordered list of modeling steps).
#
# Pydantic's ``extra="forbid"`` and ``strict=True`` reject unknown fields and
# loose types — LLM output must match this shape exactly (after sanitization).
# =============================================================================

from typing import Any, Literal

# BaseModel — data classes with validation
# ConfigDict — forbid extra JSON keys, strict typing
# Field — defaults and aliases (e.g. JSON key "from" → Python from_step)
from pydantic import BaseModel, ConfigDict, Field

# -----------------------------------------------------------------------------
# Allowed step operation names for the MVP CAD kernel
# -----------------------------------------------------------------------------
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

# High-level intent kinds the executor understands
IntentType = Literal[
    "part_create",
    "part_edit",
    "assembly_create",
    "doc_scaffold",
    "export",
    "release",
]

# Literal unions for assumptions and questions — keep LLM output bounded
AssumptionScope = Literal["part", "assembly", "project"]
AssumptionSource = Literal["user", "ai", "spec"]
AssumptionImportance = Literal["low", "medium", "high"]
AssumptionStatus = Literal["proposed", "confirmed", "rejected"]

QuestionStatus = Literal["open", "answered", "dismissed"]


class IRTarget(BaseModel):
    """What entity this intent acts on (part, assembly, or doc file)."""

    model_config = ConfigDict(extra="forbid", strict=True)

    part_id: str | None = None
    assembly_id: str | None = None
    doc_path: str | None = None


class IRContext(BaseModel):
    """Editor context: active part, selection, workspace path."""

    model_config = ConfigDict(extra="forbid", strict=True)

    active_part_id: str | None = None
    selection: list[str] = Field(default_factory=list)
    workspace_path: str | None = None


class IRQuestion(BaseModel):
    """Blocking or non-blocking question the LLM needs answered."""

    model_config = ConfigDict(extra="forbid", strict=True)

    id: str
    text: str
    blocking: bool = False
    status: QuestionStatus = "open"
    answer: str | None = None


class IRAssumption(BaseModel):
    """Design assumption (material guess, tolerance, etc.) with lifecycle status."""

    model_config = ConfigDict(extra="forbid", strict=True)

    id: str
    text: str
    scope: AssumptionScope = "part"
    source: AssumptionSource = "ai"
    importance: AssumptionImportance = "medium"
    status: AssumptionStatus = "proposed"


class IRAssemblyInstance(BaseModel):
    """One part placed in an assembly with a unique instance id."""

    model_config = ConfigDict(extra="forbid", strict=True)

    instance_id: str
    part_id: str


class IRConstraints(BaseModel):
    """Physical and assembly constraints attached to the intent."""

    model_config = ConfigDict(extra="forbid", strict=True)

    dimensions: dict[str, Any] = Field(default_factory=dict)
    material: str | None = None
    process: str | None = None
    tolerance: dict[str, Any] = Field(default_factory=dict)
    interfaces: list[str] = Field(default_factory=list)
    instances: list[IRAssemblyInstance] = Field(default_factory=list)


class IRStep(BaseModel):
    """
    One modeling operation in sequence.

    JSON uses ``"from"`` for the dependency step id; Python names it from_step
    because ``from`` is a reserved keyword.
    """

    model_config = ConfigDict(extra="forbid", strict=True, populate_by_name=True)

    id: str
    op: str
    params: dict[str, Any] = Field(default_factory=dict)
    from_step: str | None = Field(default=None, alias="from")


class IRLinks(BaseModel):
    """Traceability links to specs, requirements, architecture docs."""

    model_config = ConfigDict(extra="forbid", strict=True)

    spec_refs: list[str] = Field(default_factory=list)
    requirement_refs: list[str] = Field(default_factory=list)
    architecture_refs: list[str] = Field(default_factory=list)
    interface_refs: list[str] = Field(default_factory=list)


class IntentIR(BaseModel):
    """
    Root Intent IR document — the full modeling plan from one chat turn.

    Required: type, prompt, summary, target.
    Everything else defaults to empty collections.
    """

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
