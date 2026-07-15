# =============================================================================
# Intent IR Validator — Schema + Business Rules
# =============================================================================
#
# WHAT THIS FILE DOES
# -------------------
# After sanitization, raw dict data must become a typed IntentIR (Pydantic).
# This module checks:
#   1. Step op names are in the MVP catalog
#   2. Step dependency graph (from → id) has no duplicates or forward refs
#   3. Per-op numeric params (via ir.step_params)
#   4. Full Pydantic schema (required fields, types, strict mode)
#
# On failure it raises IntentIRValidationError with structured field_errors
# the frontend can show inline in the Problems panel.
# =============================================================================

from typing import Any

# ValidationError — Pydantic's exception when model_validate fails
from pydantic import ValidationError

# Per-op param checks (positive dimensions, etc.)
from ir.step_params import validate_step_params

# Canonical Intent IR schema and allowed step op names
from schemas.intent_ir import IntentIR, MVP_STEP_OPS


class IntentIRValidationError(Exception):
    """Structured validation failure for Intent IR — not a generic ValueError."""

    def __init__(
        self,
        message: str,
        field_errors: list[dict[str, Any]] | None = None,
        invalid_ops: list[str] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.field_errors = field_errors or []
        self.invalid_ops = invalid_ops or []

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON-RPC InvalidParams responses."""
        return {
            "message": self.message,
            "field_errors": self.field_errors,
            "invalid_ops": self.invalid_ops,
        }


def _format_pydantic_errors(exc: ValidationError) -> list[dict[str, Any]]:
    """Convert Pydantic error list into our uniform {loc, msg, type} shape."""
    return [
        {
            "loc": list(error["loc"]),
            "msg": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors()
    ]


def _validate_step_ops(steps: list[dict[str, Any]]) -> list[str]:
    """Collect op names that are not in MVP_STEP_OPS."""
    invalid_ops: list[str] = []
    for step in steps:
        op = step.get("op")
        if isinstance(op, str) and op not in MVP_STEP_OPS:
            invalid_ops.append(op)
    return invalid_ops


def _validate_step_dependency_graph(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Ensure each step's ``from`` dependency points to an earlier step id.

    Rules:
    - Duplicate step ids are errors
    - ``from`` must be a string referencing a prior step in the list
    - Forward references (depending on a later step) are errors
    """
    errors: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    ordered_ids: list[str] = []

    for index, step in enumerate(steps):
        step_id = step.get("id")
        if not isinstance(step_id, str):
            continue

        if step_id in seen_ids:
            errors.append(
                {
                    "loc": ["steps", index, "id"],
                    "msg": f"duplicate step id '{step_id}'",
                    "type": "duplicate_step_id",
                }
            )
        seen_ids.add(step_id)
        ordered_ids.append(step_id)

        from_ref = step.get("from")
        if from_ref is None:
            continue  # root step — no dependency

        if not isinstance(from_ref, str):
            errors.append(
                {
                    "loc": ["steps", index, "from"],
                    "msg": "step dependency must be a string step id",
                    "type": "invalid_step_dependency",
                }
            )
            continue

        # ordered_ids[:-1] = all ids *before* the current step
        if from_ref not in ordered_ids[:-1]:
            errors.append(
                {
                    "loc": ["steps", index, "from"],
                    "msg": f"step '{step_id}' references unknown or forward dependency '{from_ref}'",
                    "type": "invalid_step_dependency",
                }
            )

    return errors


def validate_intent_ir(data: dict[str, Any]) -> IntentIR:
    """
    Validate raw dict data and return a parsed IntentIR.

    Raises:
        IntentIRValidationError with field_errors and invalid_ops on any failure.
    """
    field_errors: list[dict[str, Any]] = []
    invalid_ops = _validate_step_ops(data.get("steps", []))

    if invalid_ops:
        field_errors.append(
            {
                "loc": ["steps"],
                "msg": f"invalid op type(s): {', '.join(sorted(set(invalid_ops)))}",
                "type": "invalid_op_type",
            }
        )

    field_errors.extend(_validate_step_dependency_graph(data.get("steps", [])))

    # Reject bad numeric params before executor / kernel see them
    field_errors.extend(validate_step_params(data.get("steps", [])))

    try:
        intent = IntentIR.model_validate(data)
    except ValidationError as exc:
        field_errors.extend(_format_pydantic_errors(exc))
        raise IntentIRValidationError(
            "Intent IR validation failed",
            field_errors=field_errors,
            invalid_ops=invalid_ops,
        ) from exc

    # Non-Pydantic checks may have accumulated errors even if model_validate passed
    if field_errors:
        raise IntentIRValidationError(
            "Intent IR validation failed",
            field_errors=field_errors,
            invalid_ops=invalid_ops,
        )

    return intent
