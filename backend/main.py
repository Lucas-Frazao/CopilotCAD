"""CopilotCAD backend entry point — JSON-RPC server over stdio."""

from __future__ import annotations

import sys
from typing import Any

from jsonrpcserver import Error, InvalidParams, Success, dispatch, method

from engine.executor import execute_intent_ir
from ir.compiler import CompileError, compile_intent as run_compile_intent
from ir.validator import IntentIRValidationError, validate_intent_ir
from llm.claude_adapter import ClaudeAdapter
from llm.errors import LLMConfigurationError
from problems.engine import evaluate_problems, problems_to_dicts

_default_adapter: ClaudeAdapter | None = None


def _get_claude_adapter() -> ClaudeAdapter:
    global _default_adapter
    if _default_adapter is None:
        _default_adapter = ClaudeAdapter()
    return _default_adapter


@method
def ping() -> Success:
    return Success("pong")


@method
def execute_intent(ir: dict[str, Any]) -> Success | Error:
    try:
        intent = validate_intent_ir(ir)
    except IntentIRValidationError as exc:
        return InvalidParams(exc.to_dict())

    result = execute_intent_ir(intent)
    problems = evaluate_problems(intent, result)
    payload = result.to_dict()
    payload["problems"] = problems_to_dicts(problems)

    if not result.success:
        return Error(-32603, result.error or "Execution failed", payload)

    return Success(payload)


@method
def compile_intent(message: str, context: dict[str, Any] | None = None) -> Success | Error:
    try:
        adapter = _get_claude_adapter()
    except LLMConfigurationError as exc:
        return Error(-32603, str(exc), {"error_type": "configuration"})

    try:
        intent = run_compile_intent(message, adapter, context)
    except CompileError as exc:
        return Error(-32603, exc.message, exc.to_dict())

    return Success(intent.model_dump(by_alias=True))


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        response = dispatch(line)
        if response:
            sys.stdout.write(response + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
