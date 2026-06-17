"""Tests for Intent IR sanitization before validation."""

from ir.sanitizer import sanitize_intent_ir_data
from ir.validator import validate_intent_ir
from test_intent_ir_validation import mounting_plate_ir


def test_sanitize_fixes_invalid_assumption_status():
    data = mounting_plate_ir()
    data["assumptions"].append(
        {
            "id": "a2",
            "text": "Corner holes are 6 mm.",
            "scope": "part",
            "source": "ai",
            "importance": "medium",
            "status": "inferred",
        }
    )
    sanitized = sanitize_intent_ir_data(data)
    intent = validate_intent_ir(sanitized)
    assert intent.assumptions[-1].status == "proposed"


def test_sanitize_moves_constraints_holes_into_dimensions():
    data = mounting_plate_ir()
    data["constraints"] = {
        "dimensions": {"length_mm": 100, "width_mm": 50, "thickness_mm": 6},
        "material": "aluminum",
        "holes": {"diameter": 6.0, "offset": 8.0},
    }
    sanitized = sanitize_intent_ir_data(data)
    intent = validate_intent_ir(sanitized)
    assert intent.constraints.dimensions["hole_diameter"] == 6.0
    assert intent.constraints.dimensions["hole_offset"] == 8.0


def test_sanitize_wraps_string_tolerance():
    data = mounting_plate_ir()
    data["constraints"] = {
        "dimensions": {"length_mm": 100},
        "material": "aluminum",
        "tolerance": "ISO 2768-m",
    }
    sanitized = sanitize_intent_ir_data(data)
    intent = validate_intent_ir(sanitized)
    assert intent.constraints.tolerance == {"standard": "ISO 2768-m"}


def test_sanitize_normalizes_llm_sketch_and_extrude_params():
    data = mounting_plate_ir()
    data["steps"] = [
        {
            "id": "s1",
            "op": "sketch_rectangle",
            "params": {"width_mm": 100, "height_mm": 50, "plane": "XY"},
        },
        {
            "id": "s2",
            "op": "extrude",
            "from": "s1",
            "params": {"depth_mm": 6, "direction": "Z"},
        },
        {
            "id": "s3",
            "op": "hole_pattern_corners",
            "from": "s2",
            "params": {"diameter_mm": 6, "offset_x_mm": 8},
        },
    ]
    sanitized = sanitize_intent_ir_data(data)
    intent = validate_intent_ir(sanitized)
    assert intent.steps[0].params["length"] == 100.0
    assert intent.steps[0].params["width"] == 50.0
    assert intent.steps[1].params["distance"] == 6.0
    assert intent.steps[1].params["direction"] == "+Z"
    assert intent.steps[2].params["diameter"] == 6.0
    assert intent.steps[2].params["offset"] == 8.0


def test_sanitize_links_list_to_object():
    data = mounting_plate_ir()
    data["target"] = {}
    data["links"] = []
    sanitized = sanitize_intent_ir_data(data)
    intent = validate_intent_ir(sanitized)
    assert intent.links.spec_refs == []
