"""Tests for OCCT bridge mounting plate golden path (F-003)."""

import pytest

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
    profile = sketch_rectangle(100.0, 50.0, "XY", "center")
    assert not profile.IsNull()


def test_extrude_returns_solid():
    profile = sketch_rectangle(100.0, 50.0, "XY", "center")
    solid = extrude(profile, 6.0, "+Z", "add")
    assert not solid.IsNull()


def test_hole_pattern_corners_returns_solid():
    profile = sketch_rectangle(100.0, 50.0, "XY", "center")
    solid = extrude(profile, 6.0, "+Z", "add")
    final = hole_pattern_corners(solid, 6.0, 8.0)
    assert not final.IsNull()


def test_mounting_plate_exports_valid_step(tmp_path):
    final = build_mounting_plate_golden()
    step_path = tmp_path / "mounting_plate.step"
    export_step(final, step_path)

    assert step_path.is_file()
    assert step_path.stat().st_size > 0

    imported = read_step(step_path)
    assert not imported.IsNull()


def test_invalid_params_raise_geometry_error():
    with pytest.raises(GeometryError, match="length must be positive"):
        sketch_rectangle(-1.0, 50.0, "XY", "center")

    with pytest.raises(GeometryError, match="plane must be one of"):
        sketch_rectangle(100.0, 50.0, "YZ", "center")
