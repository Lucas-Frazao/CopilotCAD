"""Schema and constraint validation for Intent IR."""

from typing import Any

from pydantic import ValidationError

from schemas.intent_ir import IntentIR, MVP_STEP_OPS


class IntentIRValidationError(Exception):
    """Structured validation failure for Intent IR."""

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
        return {
            "message": self.message,
            "field_errors": self.field_errors,
            "invalid_ops": self.invalid_ops,
        }


def _format_pydantic_errors(exc: ValidationError) -> list[dict[str, Any]]:
    return [
        {
            "loc": list(error["loc"]),
            "msg": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors()
    ]


def _validate_step_ops(steps: list[dict[str, Any]]) -> list[str]:
    invalid_ops: list[str] = []
    for step in steps:
        op = step.get("op")
        if isinstance(op, str) and op not in MVP_STEP_OPS:
            invalid_ops.append(op)
    return invalid_ops


def _validate_step_dependency_graph(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
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
            continue

        if not isinstance(from_ref, str):
            errors.append(
                {
                    "loc": ["steps", index, "from"],
                    "msg": "step dependency must be a string step id",
                    "type": "invalid_step_dependency",
                }
            )
            continue

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
    """Validate raw dict data and return a parsed IntentIR.

    Raises IntentIRValidationError with field errors and invalid op types on failure.
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

    dependency_errors = _validate_step_dependency_graph(data.get("steps", []))
    field_errors.extend(dependency_errors)

    try:
        intent = IntentIR.model_validate(data)
    except ValidationError as exc:
        field_errors.extend(_format_pydantic_errors(exc))
        raise IntentIRValidationError(
            "Intent IR validation failed",
            field_errors=field_errors,
            invalid_ops=invalid_ops,
        ) from exc

    if field_errors:
        raise IntentIRValidationError(
            "Intent IR validation failed",
            field_errors=field_errors,
            invalid_ops=invalid_ops,
        )

    return intent
