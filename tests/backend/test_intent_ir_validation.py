"""
test_intent_ir_validation.py — Intent IR validation unit tests (F-001)
=======================================================================

Validates the Intent IR schema: the structured JSON plan that describes what
the CAD engine should build (sketch, extrude, holes, etc.).

F-001 defines the IR contract. These tests ensure valid plans pass and broken
plans fail with clear, structured errors.

Beginner concepts:
  - Intent IR: intermediate representation between chat/LLM output and geometry.
  - validate_intent_ir: parses a dict and returns a typed IntentIR model.
  - IntentIRValidationError: raised when required fields, ops, or step deps are wrong.
"""

import pytest  # Test framework and assertion helpers

from ir.validator import IntentIRValidationError, validate_intent_ir


def mounting_plate_ir() -> dict:
    """
    Return the canonical mounting-plate Intent IR used across the test suite.

    Many other test files import this function as their golden-path sample.
    """
    return {
        "type": "part_create",
        "prompt": "Create a mounting plate 100mm by 50mm, 6mm thick, with corner mounting holes.",
        "summary": "Create mounting plate with rectangular base and corner hole pattern.",
        "target": {"part_id": "mounting_plate"},
        "context": {"active_part_id": "mounting_plate"},
        "questions": [],
        "assumptions": [
            {
                "id": "a1",
                "text": "Plate thickness is 6 mm.",
                "scope": "part",
                "source": "ai",
                "importance": "medium",
                "status": "proposed",
            }
        ],
        "constraints": {
            "dimensions": {"length_mm": 100, "width_mm": 50, "thickness_mm": 6},
            "material": "aluminum",
        },
        # Three modeling steps: sketch → extrude → corner holes
        "steps": [
            {
                "id": "s1",
                "op": "sketch_rectangle",
                "params": {
                    "length": 100.0,
                    "width": 50.0,
                    "plane": "XY",
                    "mode": "center",
                },
            },
            {
                "id": "s2",
                "op": "extrude",
                "from": "s1",  # Depends on step s1's sketch profile
                "params": {"distance": 6.0, "direction": "+Z", "mode": "add"},
            },
            {
                "id": "s3",
                "op": "hole_pattern_corners",
                "from": "s2",
                "params": {"diameter": 6.0, "offset": 8.0},
            },
        ],
        "links": {
            "spec_refs": ["mounting_plate"],
            "requirement_refs": [],
            "architecture_refs": [],
        },
    }


def test_valid_mounting_plate_ir_passes():
    """A well-formed golden IR should validate and expose typed fields."""
    intent = validate_intent_ir(mounting_plate_ir())
    assert intent.type == "part_create"
    assert intent.target.part_id == "mounting_plate"
    assert len(intent.steps) == 3
    # Step s2 should reference s1 as its input sketch
    assert intent.steps[1].from_step == "s1"


def test_missing_required_fields_fails():
    """Deleting a required top-level field (summary) must fail validation."""
    data = mounting_plate_ir()
    del data["summary"]

    with pytest.raises(IntentIRValidationError) as exc_info:
        validate_intent_ir(data)

    error = exc_info.value
    # field_errors lists every invalid location with a human-readable message
    assert any("summary" in str(item.get("loc", [])) for item in error.field_errors)


def test_invalid_op_type_fails():
    """Unknown step operations must be rejected before execution."""
    data = mounting_plate_ir()
    data["steps"][0]["op"] = "magic_extrude"

    with pytest.raises(IntentIRValidationError) as exc_info:
        validate_intent_ir(data)

    error = exc_info.value
    assert "magic_extrude" in error.invalid_ops
    assert any(item.get("type") == "invalid_op_type" for item in error.field_errors)


def test_invalid_step_dependency_fails():
    """A step cannot depend on a later step (s2 → s3 is invalid here)."""
    data = mounting_plate_ir()
    data["steps"][1]["from"] = "s3"

    with pytest.raises(IntentIRValidationError) as exc_info:
        validate_intent_ir(data)

    error = exc_info.value
    assert any(item.get("type") == "invalid_step_dependency" for item in error.field_errors)
