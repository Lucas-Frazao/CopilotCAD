"""Sequences IR steps and dispatches to handlers (F-004)."""


from engine.errors import ExecutionError, StepNotImplementedError
from engine.execution_result import ExecutionResult
from engine.handler_registry import get_handler
from schemas.intent_ir import IntentIR


def execute_intent_ir(intent: IntentIR) -> ExecutionResult:
    """Execute a validated IntentIR step-by-step and return an ExecutionResult.

    Steps run in order, each handler receiving the map of shapes produced so far.
    Never raises: dependency, not-implemented, and handler errors are captured into
    a ``success=False`` result that preserves the partially built shapes. Returns a
    ``success=True`` result with ``final_step_id`` set when all steps complete.
    """
    steps = intent.steps
    if not steps:
        return ExecutionResult(
            success=False,
            error="Intent IR has no steps to execute",
        )

    shapes: dict[str, object] = {}
    executed_ids: list[str] = []

    try:
        for step in steps:
            if step.from_step is not None and step.from_step not in shapes:
                raise ExecutionError(
                    f"step '{step.id}' references missing or forward dependency '{step.from_step}'"
                )

            handler = get_handler(step.op)
            output = handler(step, shapes)
            shapes[step.id] = output
            executed_ids.append(step.id)
    except (StepNotImplementedError, ExecutionError) as exc:
        # Expected, user-facing failures: report the message as-is and preserve
        # any partial geometry built before the failing step.
        return ExecutionResult(
            success=False,
            step_ids=executed_ids,
            error=str(exc),
            shapes_by_step_id=dict(shapes),
        )
    except Exception as exc:  # noqa: BLE001 — last-resort guard for handler defects
        # Unexpected exceptions (e.g. a bad param coercion or a kernel bug) are
        # logged to stderr for diagnosis and surfaced with an "internal" prefix
        # so the UI does not present a programming defect as ordinary user error.
        import sys
        import traceback

        print(f"[executor] unexpected error in step execution: {exc!r}", file=sys.stderr)
        traceback.print_exc()
        return ExecutionResult(
            success=False,
            step_ids=executed_ids,
            error=f"internal execution error: {type(exc).__name__}: {exc}",
            shapes_by_step_id=dict(shapes),
        )

    final_id = executed_ids[-1]
    return ExecutionResult(
        success=True,
        step_ids=executed_ids,
        final_step_id=final_id,
        shapes_by_step_id=dict(shapes),
    )
