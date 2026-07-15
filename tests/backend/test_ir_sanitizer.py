"""
test_ir_sanitizer.py — Intent IR sanitization tests
===================================================

Before validation, the sanitizer normalizes LLM output: fixes invalid enum
values, renames alternate field names, and coerces loosely typed structures
into the shape the validator expects.

These tests verify the sanitizer repairs common LLM mistakes without rejecting
the entire IR.

Beginner concepts:
  - Sanitizer: a pre-validation cleanup pass on raw LLM JSON.
  - validate_intent_ir: strict schema check after sanitization.
"""

from ir.sanitizer import sanitize_intent_ir_data
from ir.validator import validate_intent_ir
from test_intent_ir_validation import mounting_plate_ir


def test_sanitize_fixes_invalid_assumption_status():
    """
    LLMs sometimes emit status='inferred'; sanitizer should map it to 'proposed'.
    """
    data = mounting_plate_ir()
    data["assumptions"].append(
        {
            "id": "a2",
            "text": "Corner holes are 6 mm.",
            "scope": "part",
            "source": "ai",
            "importance": "medium",
            "status": "inferred",  # Not a valid enum value
        }
    )
    sanitized = sanitize_intent_ir_data(data)
    intent = validate_intent_ir(sanitized)
    assert intent.assumptions[-1].status == "proposed"


def test_sanitize_moves_constraints_holes_into_dimensions():
    """
    LLMs may put hole params under constraints.holes; sanitizer flattens them
    into constraints.dimensions with hole_diameter and hole_offset keys.
    """
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
    """A plain string tolerance becomes {"standard": "..."} object form."""
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
    """
    LLMs use alternate param names (width_mm, depth_mm, diameter_mm).
    Sanitizer maps them to canonical names (length, width, distance, offset).
    """
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
    """LLMs sometimes emit links as []; sanitizer converts to proper object form."""
    data = mounting_plate_ir()
    data["target"] = {}
    data["links"] = []
    sanitized = sanitize_intent_ir_data(data)
    intent = validate_intent_ir(sanitized)
    assert intent.links.spec_refs == []
