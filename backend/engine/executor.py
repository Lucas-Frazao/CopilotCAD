"""Sequences IR steps and dispatches to handlers (F-004)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from engine.errors import ExecutionError, StepNotImplementedError
from engine.execution_result import ExecutionResult
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
    if workspace_path is not None:
        return Path(workspace_path)
    context_path = intent.context.workspace_path
    if context_path:
        return Path(context_path)
    return None


def _assembly_instances(intent: IntentIR) -> list[dict[str, str]]:
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
    if not intent.assumptions:
        return

    path = workspace / "parts" / part_id / ASSUMPTIONS_FILENAME
    assumptions = [item.model_dump() for item in intent.assumptions]
    path.write_text(
        yaml.safe_dump({"assumptions": assumptions}, sort_keys=False),
        encoding="utf-8",
    )


def _append_execute_history(workspace: Path, part_id: str, intent: IntentIR, result: ExecutionResult) -> None:
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
    """Execute a validated IntentIR step-by-step and return an ExecutionResult."""
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

    shapes: dict[str, Any] = {}
    if workspace is not None and intent.type == "assembly_create":
        shapes.update(_preload_assembly_shapes(workspace, intent))

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
        return ExecutionResult(
            success=False,
            step_ids=executed_ids,
            error=str(exc),
            shapes_by_step_id=dict(shapes),
        )
    except Exception as exc:  # noqa: BLE001
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

    part_id = intent.target.part_id or intent.context.active_part_id
    if part_id and result.final_shape is not None:
        cache_session_shape(part_id, result.final_shape)

    return result