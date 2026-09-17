"""
Hard validation gates for Evie enclosure-class parts.

Gates (from the machine-readable spec):
  extents_within_tol, manifold_no_float, no_floating_geometry,
  faceplate_fill_band, named_cutouts_present,
  cover_hole_pattern_aligns_bosses, design_mm_only

Open tray: manifold + no floating shells. Do NOT require closed-volume watertight.
Design-mm only: never apply FDM shrink compensation.
"""

from __future__ import annotations

from typing import Any

from enclosure.constants import (
    CORNER_OFFSET_MM,
    EXTENTS_TOL_MM,
    FACEPLATE_X,
    FACEPLATE_Y,
    HOLE_ALIGN_TOL_MM,
    corner_xy_centers,
)
from enclosure.features import NamedFeature
from engine import kernel_adapter


def measure_shape(shape: Any) -> dict[str, Any]:
    """Collect bbox / volume / topology measurements via the kernel adapter."""
    xmin, ymin, zmin, xmax, ymax, zmax = kernel_adapter.shape_bbox(shape)
    dx = xmax - xmin
    dy = ymax - ymin
    dz = zmax - zmin
    volume = kernel_adapter.shape_volume(shape)
    bbox_volume = dx * dy * dz
    n_solids = kernel_adapter.count_subshapes(shape, "solid")
    n_shells = kernel_adapter.count_subshapes(shape, "shell")
    manifold = kernel_adapter.is_valid_manifold(shape)
    fraction = (volume / bbox_volume) if bbox_volume > 0 else 0.0
    return {
        "bbox": {
            "xmin": xmin,
            "ymin": ymin,
            "zmin": zmin,
            "xmax": xmax,
            "ymax": ymax,
            "zmax": zmax,
            "dx": dx,
            "dy": dy,
            "dz": dz,
        },
        "volume": volume,
        "bbox_volume": bbox_volume,
        "solid_volume_fraction": fraction,
        "n_solids": n_solids,
        "n_shells": n_shells,
        "manifold": manifold,
    }


def _gate(gate_id: str, passed: bool, detail: str, **extra: Any) -> dict[str, Any]:
    payload = {"id": gate_id, "passed": passed, "detail": detail}
    payload.update(extra)
    return payload


def _part_spec(spec: dict[str, Any], part: str) -> dict[str, Any]:
    parts = spec.get("parts") or {}
    if part not in parts:
        raise ValueError(f"spec has no part {part!r}")
    return parts[part]


def gate_extents_within_tol(part: str, spec: dict[str, Any], measured: dict[str, Any]) -> dict[str, Any]:
    part_spec = _part_spec(spec, part)
    extents = part_spec["extents"]
    tol = float(part_spec.get("extents_tol", EXTENTS_TOL_MM))
    bbox = measured["bbox"]
    checks: list[str] = []
    ok = True

    for axis, actual in (("x", bbox["dx"]), ("y", bbox["dy"])):
        target = float(extents[axis])
        delta = abs(actual - target)
        checks.append(f"{axis}: {actual:.3f} vs {target:.3f} (Δ{delta:.3f})")
        if delta > tol:
            ok = False

    z_actual = float(bbox["dz"])
    z_range = part_spec.get("extents_z_range")
    feet = part_spec.get("feet") or {}
    if z_range:
        z_min = float(z_range["min"])
        z_max = float(z_range["max"])
        z_ok = z_min - tol <= z_actual <= z_max + tol
        checks.append(f"z: {z_actual:.3f} in [{z_min}, {z_max}] (±{tol})")
        ok = ok and z_ok
        extra = {"feet_extra_z": None}
    elif feet.get("included_in_golden_bbox"):
        body_z = float(feet.get("body_z_mm", extents["z"]))
        bbox_z = float(feet.get("bbox_z_mm_approx", extents["z"]))
        z_ok = abs(z_actual - body_z) <= tol or abs(z_actual - bbox_z) <= tol
        checks.append(
            f"z: {z_actual:.3f} vs body {body_z:.3f} or golden-with-feet {bbox_z:.3f} (±{tol})"
        )
        ok = ok and z_ok
        extra = {"feet_extra_z": bbox_z - body_z}
    else:
        target_z = float(extents["z"])
        z_ok = abs(z_actual - target_z) <= tol
        checks.append(f"z: {z_actual:.3f} vs {target_z:.3f} (Δ{abs(z_actual - target_z):.3f})")
        ok = ok and z_ok
        extra = {"feet_extra_z": None}

    return _gate("extents_within_tol", ok, "; ".join(checks), **extra)


def gate_manifold_no_float(measured: dict[str, Any]) -> dict[str, Any]:
    """Manifold B-rep + single solid. Not closed-volume watertight."""
    manifold = bool(measured["manifold"])
    n_solids = int(measured["n_solids"])
    ok = manifold and n_solids == 1
    detail = (
        f"manifold={manifold}, n_solids={n_solids}, n_shells={measured['n_shells']}; "
        "open tray allowed (not closed-volume watertight)"
    )
    return _gate("manifold_no_float", ok, detail)


def gate_no_floating_geometry(measured: dict[str, Any]) -> dict[str, Any]:
    n_solids = int(measured["n_solids"])
    ok = n_solids == 1
    return _gate("no_floating_geometry", ok, f"n_solids={n_solids} (require exactly 1)")


def gate_faceplate_fill_band(part: str, spec: dict[str, Any], measured: dict[str, Any]) -> dict[str, Any]:
    if part != "faceplate":
        return _gate("faceplate_fill_band", True, f"skipped for part {part!r}", skipped=True)

    band = ((_part_spec(spec, "faceplate").get("shell") or {}).get("solid_volume_fraction")) or {}
    lo = float(band.get("min", 0.20))
    hi = float(band.get("max", 0.25))
    fraction = float(measured["solid_volume_fraction"])
    ok = lo <= fraction <= hi
    return _gate(
        "faceplate_fill_band",
        ok,
        f"solid_volume_fraction={fraction:.4f} (require {lo:.2f}–{hi:.2f})",
        measured_fraction=fraction,
        min=lo,
        max=hi,
    )


def gate_named_cutouts_present(
    part: str,
    spec: dict[str, Any],
    shape: Any,
    features: list[NamedFeature],
) -> dict[str, Any]:
    if part != "faceplate":
        return _gate("named_cutouts_present", True, f"skipped for part {part!r}", skipped=True)

    required = list(_part_spec(spec, "faceplate").get("required_named_cutouts") or [])
    by_id = {item.id: item for item in features}
    missing = [name for name in required if name not in by_id]
    probes: list[dict[str, Any]] = []
    ok = not missing

    for name in required:
        feature = by_id.get(name)
        if feature is None:
            continue
        if not feature.probe_points:
            ok = False
            probes.append({"id": name, "passed": False, "reason": "no probe points"})
            continue
        feature_ok = True
        for x, y, z in feature.probe_points:
            state = kernel_adapter.classify_point(shape, x, y, z)
            point_ok = state == "out"
            feature_ok = feature_ok and point_ok
            probes.append({"id": name, "point": [x, y, z], "state": state, "passed": point_ok})
        ok = ok and feature_ok

    detail = "missing=" + ",".join(missing) if missing else f"probed {len(required)} named cutouts"
    return _gate("named_cutouts_present", ok, detail, missing=missing, probes=probes)


def gate_cover_hole_pattern_aligns_bosses(
    part: str,
    features: list[NamedFeature],
    mate_features: list[NamedFeature] | None = None,
) -> dict[str, Any]:
    if part == "badge":
        return _gate("cover_hole_pattern_aligns_bosses", True, "skipped for badge", skipped=True)

    expected = corner_xy_centers(FACEPLATE_X, FACEPLATE_Y, CORNER_OFFSET_MM)
    if part == "cover":
        actual = [(f.cx, f.cy) for f in features if f.type == "hole"]
        source = "cover holes"
    else:
        actual = [(f.cx, f.cy) for f in features if f.type == "boss"]
        source = "faceplate bosses"

    if len(actual) != 4:
        return _gate(
            "cover_hole_pattern_aligns_bosses",
            False,
            f"{source}: expected 4 corners, found {len(actual)}",
        )

    def _matched(points: list[tuple[float, float]]) -> bool:
        unused = list(points)
        for ex, ey in expected:
            hit = None
            for index, (ax, ay) in enumerate(unused):
                if abs(ax - ex) <= HOLE_ALIGN_TOL_MM and abs(ay - ey) <= HOLE_ALIGN_TOL_MM:
                    hit = index
                    break
            if hit is None:
                return False
            unused.pop(hit)
        return True

    ok = _matched(actual)
    mate_ok = True
    if mate_features:
        mate_pts = [(f.cx, f.cy) for f in mate_features if f.type in {"hole", "boss"}]
        if len(mate_pts) == 4:
            mate_ok = _matched(mate_pts) and _matched(actual)
            # Pairwise: each actual has a mate within tol
            for ax, ay in actual:
                if not any(
                    abs(ax - mx) <= HOLE_ALIGN_TOL_MM and abs(ay - my) <= HOLE_ALIGN_TOL_MM
                    for mx, my in mate_pts
                ):
                    mate_ok = False
        ok = ok and mate_ok

    return _gate(
        "cover_hole_pattern_aligns_bosses",
        ok,
        f"{source} vs rectangular_4_corner offset={CORNER_OFFSET_MM}mm; mate_ok={mate_ok}",
        expected=expected,
        actual=actual,
    )


def gate_design_mm_only() -> dict[str, Any]:
    return _gate(
        "design_mm_only",
        True,
        "FDM shrink ignored; gates use design millimetres only (scale 100%)",
        shrink_applied=False,
    )


def run_gates(
    part: str,
    spec: dict[str, Any],
    shape: Any,
    features: list[NamedFeature] | None = None,
    mate_features: list[NamedFeature] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Return (measured, gates). ``passed`` is computed by the report builder."""
    feature_list = list(features or [])
    measured = measure_shape(shape)
    gates = [
        gate_extents_within_tol(part, spec, measured),
        gate_manifold_no_float(measured),
        gate_no_floating_geometry(measured),
        gate_faceplate_fill_band(part, spec, measured),
        gate_named_cutouts_present(part, spec, shape, feature_list),
        gate_cover_hole_pattern_aligns_bosses(part, feature_list, mate_features),
        gate_design_mm_only(),
    ]
    return measured, gates
