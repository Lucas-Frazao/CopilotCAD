"""Per-op step parameter validation at the IR layer (hardening M5).

Implemented ops carry typed parameter schemas so invalid geometry inputs
(negative/zero dimensions, missing or non-numeric params) are rejected during
validation with structured errors, instead of failing deep inside the kernel.
Stub/unimplemented ops keep permissive params.
"""

import pytest

from ir.validator import IntentIRValidationError, validate_intent_ir
from test_intent_ir_validation import mounting_plate_ir


def test_valid_golden_ir_still_passes():
    intent = validate_intent_ir(mounting_plate_ir())
    assert len(intent.steps) == 3


def test_negative_length_is_rejected():
    data = mounting_plate_ir()
    data["steps"][0]["params"]["length"] = -10.0
    with pytest.raises(IntentIRValidationError) as exc_info:
        validate_intent_ir(data)
    assert any("length" in str(item.get("loc", [])) for item in exc_info.value.field_errors)


def test_zero_distance_is_rejected():
    data = mounting_plate_ir()
    data["steps"][1]["params"]["distance"] = 0
    with pytest.raises(IntentIRValidationError):
        validate_intent_ir(data)


def test_negative_diameter_is_rejected():
    data = mounting_plate_ir()
    data["steps"][2]["params"]["diameter"] = -1.0
    with pytest.raises(IntentIRValidationError):
        validate_intent_ir(data)


def test_missing_required_param_is_rejected():
    data = mounting_plate_ir()
    del data["steps"][0]["params"]["length"]
    with pytest.raises(IntentIRValidationError):
        validate_intent_ir(data)


def test_non_numeric_dimension_is_rejected():
    data = mounting_plate_ir()
    data["steps"][1]["params"]["distance"] = "thick"
    with pytest.raises(IntentIRValidationError):
        validate_intent_ir(data)


def test_stub_op_params_remain_permissive():
    # fillet is a valid op without an implemented param schema; arbitrary params
    # must not be rejected at the IR layer.
    data = mounting_plate_ir()
    data["steps"] = [
        {"id": "s1", "op": "fillet", "params": {"radius": 2.0, "whatever": "ok"}}
    ]
    intent = validate_intent_ir(data)
    assert intent.steps[0].op == "fillet"
