"""
test_occt_bridge_mounting_plate.py — OCCT bridge golden path tests (F-003)
==========================================================================

The OCCT bridge (kernel/occt_bridge.py) is the only module allowed to import
OpenCascade (OCC) directly. These tests verify low-level geometry primitives:
sketch, extrude, hole pattern, STEP export/import.

Skipped automatically when pythonocc-core is not installed (e.g. Windows ARM64).

Beginner concepts:
  - OCCT / OpenCascade: industrial 3D geometry kernel used under the hood.
  - TopoDS_Shape: OCCT's generic 3D shape handle; IsNull() checks validity.
  - Golden path: the canonical mounting plate build sequence every test reuses.
"""

import pytest

# Skip the entire module if OpenCascade Python bindings are unavailable
pytest.importorskip("OCC.Core.TopoDS")

from kernel.occt_bridge import (
    GeometryError,
    build_mounting_plate_golden,
    export_step,
    extrude,
    hole_pattern_corners,
    read_step,
    sketch_rectangle,
)


def test_sketch_rectangle_returns_shape():
    """sketch_rectangle should return a non-null 2D profile on the XY plane."""
    profile = sketch_rectangle(100.0, 50.0, "XY", "center")
    assert not profile.IsNull()


def test_extrude_returns_solid():
    """Extruding a profile 6 mm in +Z should produce a non-null solid."""
    profile = sketch_rectangle(100.0, 50.0, "XY", "center")
    solid = extrude(profile, 6.0, "+Z", "add")
    assert not solid.IsNull()


def test_hole_pattern_corners_returns_solid():
    """Adding corner holes to the solid should still yield a valid shape."""
    profile = sketch_rectangle(100.0, 50.0, "XY", "center")
    solid = extrude(profile, 6.0, "+Z", "add")
    final = hole_pattern_corners(solid, 6.0, 8.0)
    assert not final.IsNull()


def test_mounting_plate_exports_valid_step(tmp_path):
    """
    Full golden build → STEP export → STEP re-import round-trip.

    tmp_path is pytest's temp directory for the output .step file.
    """
    final = build_mounting_plate_golden()
    step_path = tmp_path / "mounting_plate.step"
    export_step(final, step_path)

    assert step_path.is_file()
    assert step_path.stat().st_size > 0

    imported = read_step(step_path)
    assert not imported.IsNull()


def test_invalid_params_raise_geometry_error():
    """Bad inputs should raise GeometryError with a helpful message, not crash."""
    with pytest.raises(GeometryError, match="length must be positive"):
        sketch_rectangle(-1.0, 50.0, "XY", "center")

    with pytest.raises(GeometryError, match="plane must be one of"):
        sketch_rectangle(100.0, 50.0, "YZ", "center")
