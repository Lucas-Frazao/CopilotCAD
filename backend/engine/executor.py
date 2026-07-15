"""
Intent IR Executor — Run Steps End-to-End (F-004)
=================================================

WHAT THIS FILE DOES
-------------------
Takes a validated ``IntentIR`` object and runs its ``steps`` array in order.
Each step produces geometry stored in a ``shapes`` dict keyed by step id.
When done, optionally writes results to the workspace (spec, geometry, history).

MAIN ENTRY POINT
----------------
``execute_intent_ir(intent, workspace_path)`` → ``ExecutionResult``

HELPER FUNCTIONS (private, prefixed with _)
-------------------------------------------
- ``_resolve_workspace`` — find on-disk project folder from args or IR context
- ``_preload_assembly_shapes`` — load existing part geometry for assembly mates
- ``_persist_part_results`` — save spec, assumptions, geometry, history after a part run
- ``_handle_assembly_create`` — shortcut when assembly_create has no geometry steps
"""

from __future__ import annotations  # Allows forward references in type hints

import uuid  # Short unique ids for history entries
from datetime import datetime, timezone  # UTC timestamps for audit trail
from pathlib import Path  # Cross-platform file paths
from typing import Any

import yaml  # Read/write spec.yaml and assumptions.yaml

from engine.errors import ExecutionError, StepNotImplementedError
from engine.execution_result import ExecutionResult  # success, step_ids, shapes, error
from engine.handler_registry import get_handler
from project.geometry_cache import cache_session_shape, save_part_geometry
from project.part_folder import (
    ASSUMPTIONS_FILENAME,
    HISTORY_FILENAME,
    SPEC_FILENAME,
    create_part_folder,
)
from schemas.intent_ir import IntentIR


def _resolve_workspace(intent: IntentIR, workspace_path: Path | str | None) -> Path | None:
    """Pick workspace path: explicit argument wins, else IR context field."""
    if workspace_path is not None:
        return Path(workspace_path)
    context_path = intent.context.workspace_path
    if context_path:
        return Path(context_path)
    return None


def _assembly_instances(intent: IntentIR) -> list[dict[str, str]]:
    """
    Extract assembly instance list from IR.

    Tries structured ``constraints.instances`` first, then a legacy nested
    location under ``constraints.dimensions.instances``.
    """
    instances = intent.constraints.instances
    if instances:
        return [
            {"instance_id": item.instance_id, "part_id": item.part_id} for item in instances
        ]

    nested = intent.constraints.dimensions.get("instances")
    if isinstance(nested, list):
        return [
            {"instance_id": item["instance_id"], "part_id": item["part_id"]}
            for item in nested
            if isinstance(item, dict) and "instance_id" in item and "part_id" in item
        ]
    return []


def _preload_assembly_shapes(workspace: Path, intent: IntentIR) -> dict[str, Any]:
    """Load each assembly instance's part geometry into shapes[instance_id]."""
    from project.assembly_folder import read_assembly
    from project.geometry_cache import load_part_geometry

    shapes: dict[str, Any] = {}
    assembly_id = intent.target.assembly_id
    instances: list[dict[str, str]] = []

    if assembly_id:
        try:
            assembly = read_assembly(workspace, assembly_id)
            instances = assembly.get("instances", [])
        except Exception:
            instances = _assembly_instances(intent)
    else:
        instances = _assembly_instances(intent)

    for instance in instances:
        instance_id = instance["instance_id"]
        part_id = instance["part_id"]
        shape = load_part_geometry(workspace, part_id)
        if shape is not None:
            shapes[instance_id] = shape
    return shapes


def _write_spec(workspace: Path, part_id: str, intent: IntentIR) -> None:
    """Merge defaults into parts/<id>/spec.yaml without wiping existing fields."""
    spec_path = workspace / "parts" / part_id / SPEC_FILENAME
    spec: dict[str, Any] = {}
    if spec_path.is_file():
        loaded = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            spec = loaded

    spec.setdefault("part_id", part_id)
    spec.setdefault("name", part_id.replace("_", " ").title())
    spec.setdefault("maturity", "draft")
    spec.setdefault("interfaces", spec.get("interfaces", []))
    spec_path.write_text(yaml.safe_dump(spec, sort_keys=False), encoding="utf-8")


def _write_assumptions(workspace: Path, part_id: str, intent: IntentIR) -> None:
    """Overwrite assumptions.yaml when the IR carries assumption objects."""
    if not intent.assumptions:
        return

    path = workspace / "parts" / part_id / ASSUMPTIONS_FILENAME
    assumptions = [item.model_dump() for item in intent.assumptions]
    path.write_text(
        yaml.safe_dump({"assumptions": assumptions}, sort_keys=False),
        encoding="utf-8",
    )


def _append_execute_history(workspace: Path, part_id: str, intent: IntentIR, result: ExecutionResult) -> None:
    """Record an 'execute' event in parts/<id>/history.json."""
    from project.history import append_history_entry

    append_history_entry(
        workspace,
        part_id,
        {
            "id": f"exec-{uuid.uuid4().hex[:8]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "execute",
            "summary": intent.summary,
            "step_ids": list(result.step_ids),
            "assumption_ids_changed": [item.id for item in intent.assumptions],
        },
    )


def _persist_part_results(workspace: Path, intent: IntentIR, result: ExecutionResult) -> None:
    """Full persist path for part_create / part_edit intents."""
    part_id = intent.target.part_id or intent.context.active_part_id
    if not part_id:
        return

    create_part_folder(workspace, part_id)
    _write_spec(workspace, part_id, intent)
    _write_assumptions(workspace, part_id, intent)

    if result.final_shape is not None:
        save_part_geometry(workspace, part_id, result.final_shape)
    _append_execute_history(workspace, part_id, intent, result)


def _handle_assembly_create(workspace: Path | None, intent: IntentIR) -> ExecutionResult | None:
    """
    Assembly scaffold-only path: no steps means just create folders/YAML.

    Returns an ExecutionResult when handled, or None to continue normal execution.
    """
    if intent.type != "assembly_create":
        return None

    if not intent.steps:
        if workspace is not None:
            from project.assembly_folder import execute_assembly_create

            execute_assembly_create(workspace, intent.model_dump(by_alias=True))
        return ExecutionResult(success=True, step_ids=[], final_step_id=None)

    return None


def execute_intent_ir(
    intent: IntentIR,
    workspace_path: Path | str | None = None,
) -> ExecutionResult:
    """
    Execute a validated IntentIR step-by-step and return an ExecutionResult.

    Flow:
      1. Resolve workspace
      2. Handle assembly_create shortcut if applicable
      3. Loop steps: validate deps → get_handler → run → store shape
      4. Persist to disk and session cache
    """
    workspace = _resolve_workspace(intent, workspace_path)

    assembly_only = _handle_assembly_create(workspace, intent)
    if assembly_only is not None:
        return assembly_only

    steps = intent.steps
    if not steps:
        return ExecutionResult(
            success=False,
            error="Intent IR has no steps to execute",
        )

    # shapes[step_id] = OCCT shape output; also keyed by instance_id for assemblies
    shapes: dict[str, Any] = {}
    if workspace is not None and intent.type == "assembly_create":
        shapes.update(_preload_assembly_shapes(workspace, intent))

    executed_ids: list[str] = []

    try:
        for step in steps:
            # from_step must reference a step that already ran (no forward refs)
            if step.from_step is not None and step.from_step not in shapes:
                raise ExecutionError(
                    f"step '{step.id}' references missing or forward dependency '{step.from_step}'"
                )

            handler = get_handler(step.op)
            output = handler(step, shapes)
            shapes[step.id] = output
            executed_ids.append(step.id)
    except (StepNotImplementedError, ExecutionError) as exc:
        return ExecutionResult(
            success=False,
            step_ids=executed_ids,
            error=str(exc),
            shapes_by_step_id=dict(shapes),
        )
    except Exception as exc:  # noqa: BLE001
        # Unexpected bugs — log full traceback to stderr for developers
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
    result = ExecutionResult(
        success=True,
        step_ids=executed_ids,
        final_step_id=final_id,
        shapes_by_step_id=dict(shapes),
    )

    if workspace is not None:
        # After mate steps, wire interface connects_to fields in part specs
        if intent.type == "assembly_create" and any(step.op.startswith("mate_") for step in steps):
            from assembly.interface_linking import apply_interface_links_for_mate

            apply_interface_links_for_mate(workspace, intent)

        if intent.type in {"part_create", "part_edit"}:
            _persist_part_results(workspace, intent, result)
        elif intent.target.part_id or intent.context.active_part_id:
            part_id = intent.target.part_id or intent.context.active_part_id
            if part_id and result.final_shape is not None:
                create_part_folder(workspace, part_id)
                save_part_geometry(workspace, part_id, result.final_shape)

    # Session cache keeps geometry available even without a workspace write
    part_id = intent.target.part_id or intent.context.active_part_id
    if part_id and result.final_shape is not None:
        cache_session_shape(part_id, result.final_shape)

    return result
