"""Intent IR compilation pipeline (F-005)."""

from typing import Any, Literal

from ir.parser import IRParseError, parse_llm_json
from ir.validator import IntentIRValidationError, validate_intent_ir
from llm.adapter import LLMAdapter
from llm.errors import LLMConfigurationError, LLMError
from schemas.intent_ir import IntentIR

CompileErrorType = Literal["parse", "validation", "llm", "configuration"]


class CompileError(Exception):
    """Unified compile failure from LLM, parse, or validation."""

    def __init__(
        self,
        error_type: CompileErrorType,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.message = message
        self.details = details or {}

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
        raise CompileError("configuration", str(exc)) from exc
    except LLMError as exc:
        raise CompileError("llm", str(exc)) from exc

    try:
        data = parse_llm_json(raw_text)
    except IRParseError as exc:
        raise CompileError(
            "parse",
            exc.message,
            {"snippet": exc.snippet},
        ) from exc

    try:
        return validate_intent_ir(data)
    except IntentIRValidationError as exc:
        raise CompileError(
            "validation",
            exc.message,
            exc.to_dict(),
        ) from exc
