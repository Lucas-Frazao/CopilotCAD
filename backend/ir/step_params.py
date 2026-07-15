# =============================================================================
# Per-Operation Step Parameter Schemas (Hardening M5)
# =============================================================================
#
# WHAT THIS FILE DOES
# -------------------
# Each CAD "step" in Intent IR has an ``op`` (e.g. sketch_rectangle) and a
# ``params`` dict (length, width, distance, …). Pydantic models here declare
# which params are required and what values are legal (e.g. length must be > 0).
#
# WHY IT MATTERS
# --------------
# Catching bad numbers *before* the OCCT kernel runs saves time and gives the
# UI structured field errors (loc / msg / type) instead of opaque kernel crashes.
#
# Ops without a schema here are intentionally skipped — stubs stay permissive.
# =============================================================================

from __future__ import annotations

from typing import Any

# BaseModel — param schema classes
# ConfigDict — model behavior (ignore extra keys)
# Field — per-field constraints like gt=0 (greater than zero)
# ValidationError — caught and reformatted for the validator
from pydantic import BaseModel, ConfigDict, Field, ValidationError


class _BaseParams(BaseModel):
    """
    Shared base for all step param models.

    extra="ignore" means the sanitizer may leave alias keys (length_mm) alongside
    canonical keys (length); we only validate the fields declared on each subclass.
    """

    model_config = ConfigDict(extra="ignore")


class SketchRectangleParams(_BaseParams):
    """Params for ``sketch_rectangle``: a rectangle on a work plane."""

    length: float = Field(gt=0)   # must be strictly positive
    width: float = Field(gt=0)
    plane: str = "XY"             # default work plane
    mode: str = "center"          # rectangle anchored at center vs corner


class ExtrudeParams(_BaseParams):
    """Params for ``extrude``: pull a 2D profile into 3D by a distance."""

    distance: float = Field(gt=0)
    direction: str = "+Z"         # extrude along +Z by default
    mode: str = "add"             # "add" material vs "cut"


class HolePatternCornersParams(_BaseParams):
    """Params for ``hole_pattern_corners``: four holes inset from corners."""

    diameter: float = Field(gt=0)
    offset: float = Field(ge=0)   # ge=0 allows zero inset (edge-aligned holes)


# Maps op name → Pydantic param model. Only *implemented* ops appear here.
_PARAM_SCHEMAS: dict[str, type[_BaseParams]] = {
    "sketch_rectangle": SketchRectangleParams,
    "extrude": ExtrudeParams,
    "hole_pattern_corners": HolePatternCornersParams,
}


def validate_step_params(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Validate each step's params against its op schema, when registered.

    Args:
        steps: Raw step dicts from Intent IR (each has ``op`` and ``params``).

    Returns:
        List of structured field-error dicts with keys loc, msg, type.
        Empty list means every known op passed validation.
        Steps with unknown ops or non-dict params are skipped silently.
    """
    errors: list[dict[str, Any]] = []

    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            continue

        op = step.get("op")
        schema = _PARAM_SCHEMAS.get(op) if isinstance(op, str) else None
        if schema is None:
            continue  # no schema for this op yet

        params = step.get("params")
        if not isinstance(params, dict):
            params = {}

        try:
            schema.model_validate(params)
        except ValidationError as exc:
            # Flatten Pydantic errors into IR-style locations: steps[0].params.length
            for error in exc.errors():
                errors.append(
                    {
                        "loc": ["steps", index, "params", *error["loc"]],
                        "msg": error["msg"],
                        "type": f"invalid_step_param:{op}",
                    }
                )

    return errors
