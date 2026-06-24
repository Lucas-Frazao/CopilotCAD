"""Normalize common LLM Intent IR mistakes before strict validation."""

from typing import Any

_VALID_ASSUMPTION_STATUS = frozenset({"proposed", "confirmed", "rejected"})
_CONSTRAINT_KEYS = frozenset(
    {"dimensions", "material", "process", "tolerance", "interfaces", "instances"}
)


def _first_float(source: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        value = source.get(key)
        if value is not None:
            return float(value)
    return None


def _normalize_direction(value: str) -> str:
    normalized = value.strip().upper()
    if normalized == "Z":
        return "+Z"
    if normalized == "-Z":
        return "-Z"
    return value


def _dimension_map(constraints: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(constraints, dict):
        return {}
    dimensions = constraints.get("dimensions")
    return dict(dimensions) if isinstance(dimensions, dict) else {}


def _normalize_sketch_rectangle_params(
    params: dict[str, Any],
    dimensions: dict[str, Any],
) -> dict[str, Any]:
    normalized = dict(params)
    length = _first_float(normalized, "length", "length_mm")
    width = _first_float(normalized, "width", "height_mm")
    if width is None and length is not None and "width_mm" in normalized and "height_mm" in normalized:
        width = float(normalized["height_mm"])

    if length is None and "width_mm" in normalized and "height_mm" in normalized:
        length = float(normalized["width_mm"])
        if width is None:
            width = float(normalized["height_mm"])

    if length is None:
        length = _first_float(dimensions, "length_mm", "length")
    if width is None:
        width = _first_float(dimensions, "width_mm", "width", "height_mm")

    if length is not None:
        normalized["length"] = length
    if width is not None:
        normalized["width"] = width

    normalized.setdefault("plane", "XY")
    normalized.setdefault("mode", "center")
    return normalized


def _normalize_extrude_params(params: dict[str, Any], dimensions: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(params)
    distance = _first_float(normalized, "distance", "depth_mm", "thickness_mm", "depth", "height_mm")
    if distance is None:
        distance = _first_float(dimensions, "thickness_mm", "thickness", "depth_mm")

    if distance is not None:
        normalized["distance"] = distance

    direction = normalized.get("direction", "+Z")
    normalized["direction"] = _normalize_direction(str(direction))
    normalized.setdefault("mode", "add")
    return normalized


def _normalize_hole_pattern_params(params: dict[str, Any], dimensions: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(params)
    diameter = _first_float(normalized, "diameter", "diameter_mm")
    if diameter is None:
        diameter = _first_float(dimensions, "hole_diameter_mm", "hole_diameter")

    offset = _first_float(normalized, "offset", "offset_mm", "hole_offset_mm")
    if offset is None:
        offset = _first_float(normalized, "offset_x_mm", "offset_y_mm")
    if offset is None:
        offset = _first_float(dimensions, "hole_offset_mm", "hole_offset")

    if diameter is not None:
        normalized["diameter"] = diameter
    if offset is not None:
        normalized["offset"] = offset

    return normalized


def _normalize_step_params(
    op: str,
    params: dict[str, Any],
    dimensions: dict[str, Any],
) -> dict[str, Any]:
    if op == "sketch_rectangle":
        return _normalize_sketch_rectangle_params(params, dimensions)
    if op == "extrude":
        return _normalize_extrude_params(params, dimensions)
    if op == "hole_pattern_corners":
        return _normalize_hole_pattern_params(params, dimensions)
    return params


def sanitize_intent_ir_data(data: dict[str, Any]) -> dict[str, Any]:
    """Return a shallow-copied dict with known LLM schema drift corrected."""
    sanitized = dict(data)

    assumptions = sanitized.get("assumptions")
    if isinstance(assumptions, list):
        fixed_assumptions: list[dict[str, Any]] = []
        for item in assumptions:
            if not isinstance(item, dict):
                continue
            assumption = dict(item)
            if assumption.get("status") not in _VALID_ASSUMPTION_STATUS:
                assumption["status"] = "proposed"
            fixed_assumptions.append(assumption)
        sanitized["assumptions"] = fixed_assumptions

    constraints = sanitized.get("constraints")
    if isinstance(constraints, dict):
        fixed_constraints: dict[str, Any] = {}
        extra_dimensions: dict[str, Any] = {}

        for key, value in constraints.items():
            if key in _CONSTRAINT_KEYS:
                fixed_constraints[key] = value
            elif key == "holes" and isinstance(value, dict):
                for hole_key, hole_value in value.items():
                    extra_dimensions[f"hole_{hole_key}"] = hole_value
            else:
                extra_dimensions[key] = value

        if extra_dimensions:
            dimensions = fixed_constraints.get("dimensions")
            if isinstance(dimensions, dict):
                merged = dict(dimensions)
                merged.update(extra_dimensions)
                fixed_constraints["dimensions"] = merged
            else:
                fixed_constraints["dimensions"] = extra_dimensions

        tolerance = fixed_constraints.get("tolerance")
        if isinstance(tolerance, str):
            fixed_constraints["tolerance"] = {"standard": tolerance}

        interfaces = fixed_constraints.get("interfaces")
        if not isinstance(interfaces, list):
            fixed_constraints["interfaces"] = []

        sanitized["constraints"] = fixed_constraints

    links = sanitized.get("links")
    if isinstance(links, list):
        sanitized["links"] = {}

    target = sanitized.get("target")
    links = sanitized.get("links")
    if isinstance(links, dict) and isinstance(target, dict):
        part_id = target.get("part_id")
        if isinstance(part_id, str) and part_id and not links.get("spec_refs"):
            fixed_links = dict(links)
            fixed_links["spec_refs"] = [part_id]
            sanitized["links"] = fixed_links

    dimensions = _dimension_map(sanitized.get("constraints"))
    steps = sanitized.get("steps")
    if isinstance(steps, list):
        fixed_steps: list[dict[str, Any]] = []
        for step in steps:
            if not isinstance(step, dict):
                continue
            fixed_step = dict(step)
            op = fixed_step.get("op")
            params = fixed_step.get("params")
            if isinstance(op, str) and isinstance(params, dict):
                fixed_step["params"] = _normalize_step_params(op, params, dimensions)
            fixed_steps.append(fixed_step)
        sanitized["steps"] = fixed_steps

    return sanitized
