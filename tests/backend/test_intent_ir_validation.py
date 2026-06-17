"""Unit tests for Intent IR validation (F-001)."""

import pytest

from ir.validator import IntentIRValidationError, validate_intent_ir


def mounting_plate_ir() -> dict:
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
                "from": "s1",
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
    intent = validate_intent_ir(mounting_plate_ir())
    assert intent.type == "part_create"
    assert intent.target.part_id == "mounting_plate"
    assert len(intent.steps) == 3
    assert intent.steps[1].from_step == "s1"


def test_missing_required_fields_fails():
    data = mounting_plate_ir()
    del data["summary"]

    with pytest.raises(IntentIRValidationError) as exc_info:
        validate_intent_ir(data)

    error = exc_info.value
    assert any("summary" in str(item.get("loc", [])) for item in error.field_errors)


def test_invalid_op_type_fails():
    data = mounting_plate_ir()
    data["steps"][0]["op"] = "magic_extrude"

    with pytest.raises(IntentIRValidationError) as exc_info:
        validate_intent_ir(data)

    error = exc_info.value
    assert "magic_extrude" in error.invalid_ops
    assert any(item.get("type") == "invalid_op_type" for item in error.field_errors)


def test_invalid_step_dependency_fails():
    data = mounting_plate_ir()
    data["steps"][1]["from"] = "s3"

    with pytest.raises(IntentIRValidationError) as exc_info:
        validate_intent_ir(data)

    error = exc_info.value
    assert any(item.get("type") == "invalid_step_dependency" for item in error.field_errors)
