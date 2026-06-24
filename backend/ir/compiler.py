"""Intent IR compilation pipeline (F-005)."""

from typing import Any, Literal

from ir.parser import IRParseError, parse_llm_json
from ir.sanitizer import sanitize_intent_ir_data
from ir.validator import IntentIRValidationError, validate_intent_ir
from llm.adapter import LLMAdapter
from llm.errors import LLMConfigurationError, LLMError
from schemas.intent_ir import IntentIR

CompileErrorType = Literal["parse", "validation", "llm", "configuration"]


class CompileError(Exception):
    """Unified compile failure from LLM, parse, or validation."""

    def __init__(
        self,
        message: str,
        *,
        error_type: CompileErrorType = "validation",
        details: dict[str, Any] | None = None,
        field_errors: list[dict[str, Any]] | None = None,
    ) -> None:
        resolved_details = dict(details or {})
        if field_errors is not None:
            resolved_details["field_errors"] = field_errors

        super().__init__(message)
        self.error_type = error_type
        self.message = message
        self.details = resolved_details

    def to_dict(self) -> dict[str, Any]:
        return {
            "error_type": self.error_type,
            "message": self.message,
            "details": self.details,
        }


def compile_intent(
    user_message: str,
    adapter: LLMAdapter,
    project_context: dict[str, Any] | None = None,
) -> IntentIR:
    """Run LLM → parse → validate and return IntentIR."""
    try:
        raw_text = adapter.generate_structured_json(user_message, project_context)
    except LLMConfigurationError as exc:
        raise CompileError(str(exc), error_type="configuration") from exc
    except LLMError as exc:
        raise CompileError(str(exc), error_type="llm") from exc

    try:
        data = parse_llm_json(raw_text)
    except IRParseError as exc:
        raise CompileError(
            exc.message,
            error_type="parse",
            details={"snippet": exc.snippet},
        ) from exc

    try:
        return validate_intent_ir(sanitize_intent_ir_data(data))
    except IntentIRValidationError as exc:
        raise CompileError(
            exc.message,
            error_type="validation",
            details=exc.to_dict(),
        ) from exc
