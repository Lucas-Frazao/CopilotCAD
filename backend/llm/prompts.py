"""System prompts for Intent IR generation (F-005)."""

from schemas.intent_ir import MVP_STEP_OPS

_INTENT_TYPES = (
    "part_create",
    "part_edit",
    "assembly_create",
    "doc_scaffold",
    "export",
    "release",
)


def build_system_prompt() -> str:
    ops_sorted = ", ".join(sorted(MVP_STEP_OPS))
    types_sorted = ", ".join(_INTENT_TYPES)

    return (
        "You are the CopilotCAD Intent IR compiler. "
        "Convert the user's CAD request into a single JSON object matching the slim Intent IR schema. "
        "Respond with ONLY a JSON object — no markdown, no commentary, no code fences.\n\n"
        "Required top-level fields:\n"
        "- type: one of " + types_sorted + "\n"
        "- prompt: copy of the user's message\n"
        "- summary: short execution summary\n"
        "- target: object with optional part_id, assembly_id, doc_path\n"
        "- context, questions, assumptions, constraints, steps, links: optional (use [] or {} when empty)\n\n"
        "assumptions[]: each item MUST be an object: "
        '{"id": "a1", "text": "...", "scope": "part", "source": "ai", "importance": "medium", "status": "proposed"}\n'
        "constraints: MUST be an object like "
        '{"dimensions": {"length_mm": 100}, "material": "aluminum"} — never a list of strings.\n'
        "links: MUST be an object like "
        '{"spec_refs": [], "requirement_refs": [], "architecture_refs": []} — never an empty list.\n\n'
        "Each step in steps[] must have:\n"
        "- id: unique string within the IR\n"
        "- op: one of the MVP ops listed below\n"
        "- params: object with op-specific parameters\n"
        "- from: optional string referencing a prior step id (required for ops that need input geometry)\n\n"
        "Step dependency rule: 'from' must reference a step id that appears earlier in the steps array.\n"
        "Units: millimeters for all dimensions unless the user specifies otherwise.\n\n"
        "Valid step ops:\n"
        f"{ops_sorted}\n\n"
        "Example mounting plate (100x50x6 mm, corner holes 6 mm diameter, 8 mm offset):\n"
        "steps: sketch_rectangle → extrude → hole_pattern_corners with matching params.\n"
        "Use part_create for new parts. Propose assumptions in assumptions[] when inferring dimensions."
    )
