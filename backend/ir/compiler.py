# =============================================================================
# Intent IR Compiler Pipeline (Feature F-005)
# =============================================================================
#
# WHAT THIS FILE DOES
# -------------------
# Turns natural language into a validated IntentIR in three stages:
#
#   User message  →  LLM (JSON text)  →  parse  →  sanitize  →  validate  →  IntentIR
#
# All failure modes are wrapped in CompileError so main.py and the error catalog
# can return consistent JSON-RPC errors to the frontend.
# =============================================================================

from typing import Any, Literal

# Stage 2: extract JSON object from LLM markdown/text
from ir.parser import IRParseError, parse_llm_json

# Stage 3a: fix LLM alias drift
from ir.sanitizer import sanitize_intent_ir_data

# Stage 3b: strict schema + step rules
from ir.validator import IntentIRValidationError, validate_intent_ir

# Protocol implemented by ClaudeAdapter (and test fakes)
from llm.adapter import LLMAdapter
from llm.errors import LLMConfigurationError, LLMError

# Output type — typed Pydantic model
from schemas.intent_ir import IntentIR

# Categories surfaced in error catalog and RPC payloads
CompileErrorType = Literal["parse", "validation", "llm", "configuration"]


class CompileError(Exception):
    """
    Unified compile failure from LLM, parse, or validation.

    error_type maps to catalog keys like compile_parse, compile_validation.
    """

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
        """JSON-serializable error payload for RPC responses."""
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
    """
    Run LLM → parse → sanitize → validate and return IntentIR.

    Args:
        user_message: Chat text from the user.
        adapter: LLM backend (typically ClaudeAdapter).
        project_context: Optional workspace/part hints for the prompt.

    Raises:
        CompileError on any stage failure (never raw IRParseError / ValidationError).
    """
    # --- Stage 1: Ask the LLM for structured JSON text ---
    try:
        raw_text = adapter.generate_structured_json(user_message, project_context)
    except LLMConfigurationError as exc:
        raise CompileError(str(exc), error_type="configuration") from exc
    except LLMError as exc:
        raise CompileError(str(exc), error_type="llm") from exc

    # --- Stage 2: Parse text → dict ---
    try:
        data = parse_llm_json(raw_text)
    except IRParseError as exc:
        raise CompileError(
            exc.message,
            error_type="parse",
            details={"snippet": exc.snippet},
        ) from exc

    # --- Stage 3: Sanitize aliases, then validate to IntentIR ---
    try:
        return validate_intent_ir(sanitize_intent_ir_data(data))
    except IntentIRValidationError as exc:
        raise CompileError(
            exc.message,
            error_type="validation",
            details=exc.to_dict(),
        ) from exc
