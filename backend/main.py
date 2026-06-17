"""CopilotCAD backend entry point — JSON-RPC server over stdio."""

from __future__ import annotations

import sys
from typing import Any

from jsonrpcserver import Error, InvalidParams, Success, dispatch, method

from engine.executor import execute_intent_ir
from ir.validator import IntentIRValidationError, validate_intent_ir


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
    if not result.success:
        return Error(-32603, result.error or "Execution failed", result.to_dict())

    return Success(result.to_dict())


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
