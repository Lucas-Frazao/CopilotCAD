"""Per-op step parameter schemas for IR validation (hardening M5).

Implemented step ops declare a Pydantic model describing their required params and
value constraints (e.g. positive dimensions). Running these at validation time means
geometrically impossible inputs are rejected with structured field errors before the
executor or kernel is ever reached. Ops without a schema here (stubs and not-yet-
implemented ops) keep permissive params and are skipped.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class _BaseParams(BaseModel):
    # extra="ignore": the sanitizer may leave original aliases (e.g. length_mm)
    # alongside the canonical keys; only the declared params matter to handlers.
    model_config = ConfigDict(extra="ignore")


class SketchRectangleParams(_BaseParams):
    """Params for ``sketch_rectangle``: a centered/cornered planar rectangle."""

    length: float = Field(gt=0)
    width: float = Field(gt=0)
    plane: str = "XY"
    mode: str = "center"


class ExtrudeParams(_BaseParams):
    """Params for ``extrude``: linear extrusion of a profile by a distance."""

    distance: float = Field(gt=0)
    direction: str = "+Z"
    mode: str = "add"


class HolePatternCornersParams(_BaseParams):
    """Params for ``hole_pattern_corners``: four corner holes inset from edges."""

    diameter: float = Field(gt=0)
    offset: float = Field(ge=0)


# Maps op name → param model. Only implemented ops appear here; everything else
# is intentionally absent so stub ops are not constrained.
_PARAM_SCHEMAS: dict[str, type[_BaseParams]] = {
    "sketch_rectangle": SketchRectangleParams,
    "extrude": ExtrudeParams,
    "hole_pattern_corners": HolePatternCornersParams,
}


def validate_step_params(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Validate each step's params against its op schema, if one is registered.

    Args:
        steps: raw step dicts from the IR (each with ``op`` and ``params``).

    Returns:
        A list of structured field-error dicts (``loc``/``msg``/``type``), empty
        when every step with a known schema has valid params. Steps whose op has
        no schema, or whose params are not a dict, are skipped.
    """
    errors: list[dict[str, Any]] = []
    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            continue
        op = step.get("op")
        schema = _PARAM_SCHEMAS.get(op) if isinstance(op, str) else None
        if schema is None:
            continue
        params = step.get("params")
        if not isinstance(params, dict):
            params = {}
        try:
            schema.model_validate(params)
        except ValidationError as exc:
            for error in exc.errors():
                errors.append(
                    {
                        "loc": ["steps", index, "params", *error["loc"]],
                        "msg": error["msg"],
                        "type": f"invalid_step_param:{op}",
                    }
                )
    return errors
