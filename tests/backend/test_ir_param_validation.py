"""
test_ir_param_validation.py — Per-op step parameter validation (hardening M5)
=============================================================================

Implemented CAD operations (sketch_rectangle, extrude, hole_pattern_corners)
carry typed parameter schemas. Invalid geometry inputs — negative dimensions,
missing params, non-numeric values — must be rejected at the IR layer with
structured errors, not deep inside the OCCT kernel.

Stub/unimplemented ops (like fillet) keep permissive params until implemented.

Beginner concepts:
  - IR layer: validation happens on the JSON plan before any geometry runs.
  - IntentIRValidationError: carries field_errors listing each bad param location.
"""

import pytest

from ir.validator import IntentIRValidationError, validate_intent_ir
from test_intent_ir_validation import mounting_plate_ir


def test_valid_golden_ir_still_passes():
    """Sanity check: the canonical mounting plate IR still validates cleanly."""
    intent = validate_intent_ir(mounting_plate_ir())
    assert len(intent.steps) == 3


def test_negative_length_is_rejected():
    """Negative sketch length must fail with an error pointing at 'length'."""
    data = mounting_plate_ir()
    data["steps"][0]["params"]["length"] = -10.0
    with pytest.raises(IntentIRValidationError) as exc_info:
        validate_intent_ir(data)
    assert any("length" in str(item.get("loc", [])) for item in exc_info.value.field_errors)


def test_zero_distance_is_rejected():
    """Zero extrude distance is not valid geometry — reject at validation."""
    data = mounting_plate_ir()
    data["steps"][1]["params"]["distance"] = 0
    with pytest.raises(IntentIRValidationError):
        validate_intent_ir(data)


def test_negative_diameter_is_rejected():
    """Hole diameter must be positive."""
    data = mounting_plate_ir()
    data["steps"][2]["params"]["diameter"] = -1.0
    with pytest.raises(IntentIRValidationError):
        validate_intent_ir(data)


def test_missing_required_param_is_rejected():
    """Deleting a required param (length on sketch_rectangle) must fail."""
    data = mounting_plate_ir()
    del data["steps"][0]["params"]["length"]
    with pytest.raises(IntentIRValidationError):
        validate_intent_ir(data)


def test_non_numeric_dimension_is_rejected():
    """String values where numbers are expected must be rejected."""
    data = mounting_plate_ir()
    data["steps"][1]["params"]["distance"] = "thick"
    with pytest.raises(IntentIRValidationError):
        validate_intent_ir(data)


def test_stub_op_params_remain_permissive():
    """
    fillet is a valid op name but has no strict param schema yet.
    Arbitrary extra params must not be rejected at the IR layer.
    """
    data = mounting_plate_ir()
    data["steps"] = [
        {"id": "s1", "op": "fillet", "params": {"radius": 2.0, "whatever": "ok"}}
    ]
    intent = validate_intent_ir(data)
    assert intent.steps[0].op == "fillet"
