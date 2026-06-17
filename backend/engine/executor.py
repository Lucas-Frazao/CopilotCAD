"""Sequences IR steps and dispatches to handlers (F-004)."""

from engine.errors import ExecutionError, StepNotImplementedError
from engine.execution_result import ExecutionResult
from engine.handler_registry import get_handler
from schemas.intent_ir import IntentIR


def execute_intent_ir(intent: IntentIR) -> ExecutionResult:
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
    except StepNotImplementedError as exc:
        return ExecutionResult(
            success=False,
            step_ids=executed_ids,
            error=str(exc),
            shapes_by_step_id=dict(shapes),
        )
    except (ExecutionError, Exception) as exc:
        return ExecutionResult(
            success=False,
            step_ids=executed_ids,
            error=str(exc),
            shapes_by_step_id=dict(shapes),
        )

    final_id = executed_ids[-1]
    return ExecutionResult(
        success=True,
        step_ids=executed_ids,
        final_step_id=final_id,
        shapes_by_step_id=dict(shapes),
    )
