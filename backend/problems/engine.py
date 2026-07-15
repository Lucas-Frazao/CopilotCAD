"""
Problems Engine — Structured Issue Detection (F-006)
======================================================

WHAT THIS FILE DOES
-------------------
After Intent IR is built (and optionally executed), this module scans for
issues that should surface in the Problems panel: blocking questions, failed
geometry, mate errors, traceability gaps, etc.

OUTPUT
------
List of ``Problem`` Pydantic objects (serialized to dicts via problems_to_dicts).

CHECK FUNCTIONS (private)
---------------------------
Each ``_check_*`` returns zero or more Problems for one concern area.
``evaluate_problems`` runs all checks and concatenates results.
"""

from typing import Any

from engine.execution_result import ExecutionResult
from schemas.intent_ir import IntentIR
from schemas.problem import Problem


def problems_to_dicts(problems: list[Problem]) -> list[dict[str, Any]]:
    """Convert Problem models to plain dicts for JSON-RPC."""
    return [problem.model_dump() for problem in problems]


def _part_id(intent: IntentIR) -> str | None:
    return intent.target.part_id


def _check_missing_required_input(intent: IntentIR) -> list[Problem]:
    """Blocking open questions prevent safe execution."""
    problems: list[Problem] = []
    part_id = _part_id(intent)
    for question in intent.questions:
        if question.blocking and question.status == "open":
            problems.append(
                Problem(
                    id=f"missing_required_input:{question.id}",
                    type="missing_required_input",
                    severity="blocking",
                    message=f"Blocking question is unanswered: {question.text}",
                    part_id=part_id,
                    suggested_next_steps=[
                        "Answer the blocking question in chat.",
                        "Dismiss the question if it no longer applies.",
                    ],
                )
            )
    return problems


def _check_unresolved_assumption(intent: IntentIR) -> list[Problem]:
    """High-importance assumptions still in 'proposed' state warrant a warning."""
    problems: list[Problem] = []
    part_id = _part_id(intent)
    for assumption in intent.assumptions:
        if assumption.importance == "high" and assumption.status == "proposed":
            problems.append(
                Problem(
                    id=f"unresolved_assumption:{assumption.id}",
                    type="unresolved_assumption",
                    severity="warning",
                    message=f"High-importance assumption is still proposed: {assumption.text}",
                    part_id=part_id,
                    suggested_next_steps=[
                        "Confirm or reject the assumption in chat.",
                        "Lower importance if the assumption is optional.",
                    ],
                )
            )
    return problems


def _check_geometry_generation_failure(
    execution_result: ExecutionResult | None,
) -> list[Problem]:
    """Map executor failure to a user-visible geometry error."""
    if execution_result is None or execution_result.success:
        return []

    detail = execution_result.error or "Geometry execution failed"
    return [
        Problem(
            id="geometry_generation_failure:global",
            type="geometry_generation_failure",
            severity="error",
            message=f"Geometry generation failed: {detail}",
            suggested_next_steps=[
                "Review step parameters in the Intent IR.",
                "Check that all step ops are implemented for this feature.",
            ],
        )
    ]


def _check_interface_conflict(intent: IntentIR) -> list[Problem]:
    """Duplicate interface names in assembly constraints are ambiguous."""
    if intent.type != "assembly_create":
        return []

    interfaces = intent.constraints.interfaces
    if len(interfaces) < 2:
        return []

    seen: set[str] = set()
    duplicates: set[str] = set()
    for name in interfaces:
        if name in seen:
            duplicates.add(name)
        seen.add(name)

    if not duplicates:
        return []

    dup_list = ", ".join(sorted(duplicates))
    return [
        Problem(
            id=f"interface_conflict:{_part_id(intent) or 'global'}",
            type="interface_conflict",
            severity="error",
            message=f"Duplicate interface identifiers in assembly IR: {dup_list}",
            part_id=_part_id(intent),
            suggested_next_steps=[
                "Use unique interface names for each mating connection.",
                "Review assembly constraints.interfaces in the IR.",
            ],
        )
    ]


def _check_invalid_mate(intent: IntentIR) -> list[Problem]:
    """Mate steps should include target and mate_type in params (future solver)."""
    problems: list[Problem] = []
    part_id = _part_id(intent)
    for step in intent.steps:
        if not step.op.startswith("mate_"):
            continue
        params = step.params
        missing_target = "target" not in params
        missing_mate_type = "mate_type" not in params
        if missing_target or missing_mate_type:
            problems.append(
                Problem(
                    id=f"invalid_mate:{step.id}",
                    type="invalid_mate",
                    severity="error",
                    message=f"Mate step '{step.id}' ({step.op}) has incomplete mate parameters",
                    part_id=part_id,
                    step_id=step.id,
                    suggested_next_steps=[
                        "Add target and mate_type to mate step params.",
                        "Verify mate references valid geometry or interface ids.",
                    ],
                )
            )
    return problems


def _check_manufacturing_rule_warning(intent: IntentIR) -> list[Problem]:
    """Process set without dimensions cannot be validated against limits."""
    if not intent.constraints.process:
        return []

    if intent.constraints.dimensions:
        return []

    part_id = _part_id(intent)
    return [
        Problem(
            id=f"manufacturing_rule_warning:{part_id or 'global'}",
            type="manufacturing_rule_warning",
            severity="warning",
            message=(
                f"Manufacturing process '{intent.constraints.process}' is set "
                "but no dimensions were provided to validate process limits"
            ),
            part_id=part_id,
            suggested_next_steps=[
                "Add dimensions to constraints.dimensions.",
                "Confirm process limits in manufacturing_stack docs.",
            ],
        )
    ]


def _check_traceability_gap(intent: IntentIR) -> list[Problem]:
    """Parts should link to spec_refs for requirements traceability."""
    if intent.type not in {"part_create", "part_edit"}:
        return []

    part_id = _part_id(intent)
    if not part_id:
        return []

    if intent.links.spec_refs:
        return []

    return [
        Problem(
            id=f"traceability_gap:{part_id}",
            type="traceability_gap",
            severity="warning",
            message=f"Part '{part_id}' has no spec_refs in links for traceability",
            part_id=part_id,
            suggested_next_steps=[
                "Add part id to links.spec_refs.",
                "Create or link spec.yaml for this part.",
            ],
        )
    ]


def evaluate_problems(
    intent: IntentIR,
    execution_result: ExecutionResult | None = None,
) -> list[Problem]:
    """Compute MVP problems from Intent IR and optional execution outcome."""
    problems: list[Problem] = []
    problems.extend(_check_missing_required_input(intent))
    problems.extend(_check_unresolved_assumption(intent))
    problems.extend(_check_geometry_generation_failure(execution_result))
    problems.extend(_check_interface_conflict(intent))
    problems.extend(_check_invalid_mate(intent))
    problems.extend(_check_manufacturing_rule_warning(intent))
    problems.extend(_check_traceability_gap(intent))
    return problems
