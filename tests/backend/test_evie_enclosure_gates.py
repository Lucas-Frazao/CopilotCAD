"""
test_evie_enclosure_gates.py — Evie enclosure dogfood gates and builders
=======================================================================

Hard gates must reject an ~80% solid brick and accept a proper open-tray
shell. Badge + cover generate/validate is the week-1 smoke path.

Skipped when pythonocc-core is unavailable.
"""

from __future__ import annotations

import json

import pytest

pytest.importorskip("OCC.Core.TopoDS")

from enclosure.builders import build_approx_brick, build_faceplate
from enclosure.gates import measure_shape, run_gates
from enclosure.report import build_report
from enclosure.service import export_part, generate_part, validate_part
from enclosure.spec_loader import load_enclosure_spec


def _gate(report: dict, gate_id: str) -> dict:
    for item in report["gates"]:
        if item["id"] == gate_id:
            return item
    raise AssertionError(f"missing gate {gate_id}")


def test_spec_loader_reads_checked_in_yaml():
    spec = load_enclosure_spec()
    assert spec["project"] == "Evie"
    assert spec["parts"]["faceplate"]["required_named_cutouts"] == [
        "pico_bay",
        "mute",
        "mic",
        "speaker",
        "status_led",
        "hid_usbc",
    ]


def test_faceplate_fill_band_rejects_80pct_brick():
    spec = load_enclosure_spec()
    brick = build_approx_brick(0.80)
    measured = measure_shape(brick.shape)
    assert 0.70 <= measured["solid_volume_fraction"] <= 0.90

    measured, gates = run_gates("faceplate", spec, brick.shape, features=brick.features)
    report = build_report("faceplate", spec, measured, gates, brick.features)
    fill = _gate(report, "faceplate_fill_band")
    assert fill["passed"] is False
    assert report["passed"] is False
    cutouts = _gate(report, "named_cutouts_present")
    assert cutouts["passed"] is False


def test_faceplate_shell_passes_fill_band_and_cutouts():
    spec = load_enclosure_spec()
    shell = build_faceplate()
    measured, gates = run_gates("faceplate", spec, shell.shape, features=shell.features)
    report = build_report("faceplate", spec, measured, gates, shell.features)
    assert 0.20 <= measured["solid_volume_fraction"] <= 0.25
    assert _gate(report, "faceplate_fill_band")["passed"] is True
    assert _gate(report, "named_cutouts_present")["passed"] is True
    assert _gate(report, "manifold_no_float")["passed"] is True
    assert _gate(report, "extents_within_tol")["passed"] is True
    assert _gate(report, "design_mm_only")["passed"] is True
    assert report["passed"] is True


def test_badge_and_cover_generate_validate_smoke():
    badge = validate_part("badge")
    cover = validate_part("cover")
    assert badge["passed"] is True
    assert cover["passed"] is True
    assert _gate(cover, "cover_hole_pattern_aligns_bosses")["passed"] is True
    assert _gate(badge, "extents_within_tol")["passed"] is True


def test_cover_holes_mate_faceplate_bosses():
    faceplate = generate_part("faceplate")
    cover = generate_part("cover")
    report = validate_part(
        "cover",
        artifact_id=cover["artifact_id"],
        mate_artifact_id=faceplate["artifact_id"],
    )
    assert report["passed"] is True
    assert _gate(report, "cover_hole_pattern_aligns_bosses")["passed"] is True


def test_cli_report_is_json_schema_v1(tmp_path):
    report = validate_part("badge")
    assert report["schema"] == "copilotcad.enclosure.gate_report.v1"
    path = tmp_path / "badge.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["part"] == "badge"
    assert loaded["design_mm_only"] is True


def test_export_step_and_stl(tmp_path):
    generated = generate_part("badge")
    step = export_part("step", tmp_path / "badge.step", artifact_id=generated["artifact_id"])
    stl = export_part("stl", tmp_path / "badge.stl", artifact_id=generated["artifact_id"])
    assert step["bytes"] > 0
    assert stl["bytes"] > 0
    assert (tmp_path / "badge.step").is_file()
    assert (tmp_path / "badge.stl").is_file()
