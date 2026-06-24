"""CopilotCAD backend entry point — JSON-RPC server over stdio."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from jsonrpcserver import Error, InvalidParams, Success, dispatch, method

from approval.pending_store import PendingIntentStore, reject_pending
from approval.risk_classifier import classify_intent_risk
from commands.slash_handlers import handle_slash_command as run_slash_command
from engine.executor import execute_intent_ir
from ir.compiler import CompileError, compile_intent as run_compile_intent
from ir.validator import IntentIRValidationError, validate_intent_ir
from llm.claude_adapter import ClaudeAdapter
from llm.errors import LLMConfigurationError
from problems.engine import evaluate_problems, problems_to_dicts
from project.assumptions import AssumptionError, update_assumption as update_part_assumption
from project.export_polish import (
    ExportError,
    export_assembly as export_assembly_file,
    export_part_with_history,
)
from project.geometry_cache import load_part_geometry
from project.history import get_part_history as read_part_history
from project.interfaces_list import list_interfaces as build_interfaces_list
from project.parts_list import list_parts as build_parts_list
from project.workspace import WorkspaceError, create_workspace as init_workspace, load_workspace
from project.workspace_tree import (
    WorkspacePathError,
    list_workspace_tree as build_workspace_tree,
    read_workspace_file as read_workspace_text,
)
from workspace.capabilities import capabilities_payload, check_capability

_default_adapter: ClaudeAdapter | None = None
_pending_store = PendingIntentStore()


def _get_claude_adapter() -> ClaudeAdapter:
    global _default_adapter
    if _default_adapter is None:
        _default_adapter = ClaudeAdapter()
    return _default_adapter


@method
def ping() -> Success:
    return Success("pong")


@method
def execute_intent(
    ir: dict[str, Any],
    workspace_path: str | None = None,
) -> Success | Error:
    try:
        intent = validate_intent_ir(ir)
    except IntentIRValidationError as exc:
        return InvalidParams(exc.to_dict())

    result = execute_intent_ir(intent, workspace_path=workspace_path)
    problems = evaluate_problems(intent, result)
    payload = result.to_dict()
    payload["problems"] = problems_to_dicts(problems)

    if not result.success:
        return Error(-32603, result.error or "Execution failed", payload)

    return Success(payload)


@method
def compile_intent(message: str, context: dict[str, Any] | None = None) -> Success | Error:
    from pdd.classifier import build_pdd_suggestion_payload, classify_request_complexity

    complexity = classify_request_complexity(message, context)
    if complexity["classification"] == "suggest_pdd":
        return Success(build_pdd_suggestion_payload(message))

    try:
        adapter = _get_claude_adapter()
    except LLMConfigurationError as exc:
        return Error(-32603, str(exc), {"error_type": "configuration"})

    try:
        intent = run_compile_intent(message, adapter, context)
    except CompileError as exc:
        return Error(-32603, exc.message, exc.to_dict())

    intent_dict = intent.model_dump(by_alias=True)
    if classify_intent_risk(intent_dict) == "high":
        pending_id = _pending_store.add(intent_dict)
        return Success({"pending": True, "pending_id": pending_id, "intent": intent_dict})

    return Success(intent_dict)


@method
def list_workspace_tree(workspace_path: str) -> Success | Error:
    try:
        tree = build_workspace_tree(Path(workspace_path))
    except WorkspaceError as exc:
        return Error(-32602, str(exc))

    return Success(tree)


@method
def read_workspace_file(workspace_path: str, relative_path: str) -> Success | Error:
    try:
        contents = read_workspace_text(Path(workspace_path), relative_path)
    except WorkspacePathError as exc:
        return Error(-32602, str(exc))
    except WorkspaceError as exc:
        return Error(-32602, str(exc))

    return Success({"contents": contents})


@method
def get_part_mesh(workspace_path: str, part_id: str) -> Success | Error:
    from mesh.part_mesh import build_part_mesh_payload

    shape = load_part_geometry(Path(workspace_path), part_id)
    if shape is None:
        return Error(-32602, f"No geometry for part '{part_id}'")
    return Success(build_part_mesh_payload(shape))


@method
def get_assembly_mesh(workspace_path: str, assembly_id: str) -> Success | Error:
    from mesh.assembly_mesh import build_assembly_mesh_payload

    try:
        payload = build_assembly_mesh_payload(Path(workspace_path), assembly_id)
    except Exception as exc:  # noqa: BLE001
        return Error(-32602, str(exc))
    return Success(payload)


@method
def list_parts(workspace_path: str) -> Success | Error:
    return Success(build_parts_list(Path(workspace_path)))


@method
def list_interfaces(workspace_path: str) -> Success | Error:
    return Success(build_interfaces_list(Path(workspace_path)))


@method
def get_part_history(workspace_path: str, part_id: str) -> Success | Error:
    return Success(read_part_history(Path(workspace_path), part_id))


@method
def handle_slash_command(
    command: str,
    workspace_path: str,
    active_part_id: str | None = None,
) -> Success | Error:
    context = {"workspace_path": workspace_path}
    if active_part_id:
        context["active_part_id"] = active_part_id
    result = run_slash_command(command, context)
    if not result.get("success"):
        return Error(-32602, result.get("error", "Slash command failed"), result)
    return Success(result)


@method
def update_assumption(
    workspace_path: str,
    part_id: str,
    assumption_id: str,
    status: str,
    text: str | None = None,
) -> Success | Error:
    try:
        updated = update_part_assumption(
            Path(workspace_path),
            part_id,
            assumption_id,
            status,
            text=text,
        )
    except AssumptionError as exc:
        return Error(-32602, str(exc))
    return Success(updated)


@method
def approve_intent(pending_id: str, workspace_path: str | None = None) -> Success | Error:
    intent = _pending_store.get(pending_id)
    if intent is None:
        return Error(-32602, f"Unknown pending_id: {pending_id}")

    validated = validate_intent_ir(intent)
    result = execute_intent_ir(validated, workspace_path=workspace_path)
    if not result.success:
        return Error(-32603, result.error or "Execution failed", result.to_dict())

    _pending_store.mark_executed(pending_id)
    return Success(result.to_dict())


@method
def reject_intent(
    pending_id: str,
    workspace_path: str | None = None,
) -> Success | Error:
    try:
        reject_pending(
            _pending_store,
            pending_id,
            workspace_path=Path(workspace_path) if workspace_path else None,
        )
    except KeyError:
        return Error(-32602, f"Unknown pending_id: {pending_id}")
    return Success({"rejected": True, "pending_id": pending_id})


@method
def export_part(
    workspace_path: str,
    part_id: str,
    format: str = "step",
) -> Success | Error:
    try:
        path = export_part_with_history(Path(workspace_path), part_id, format=format)  # type: ignore[arg-type]
    except ExportError as exc:
        return Error(-32602, str(exc))
    return Success({"path": str(path)})


@method
def export_assembly(
    workspace_path: str,
    assembly_id: str,
    format: str = "step",
) -> Success | Error:
    try:
        path = export_assembly_file(Path(workspace_path), assembly_id, format=format)  # type: ignore[arg-type]
    except ExportError as exc:
        return Error(-32602, str(exc))
    return Success({"path": str(path)})


@method
def create_workspace(path: str, project_name: str) -> Success | Error:
    try:
        manifest = init_workspace(Path(path), project_name)
    except OSError as exc:
        return Error(-32603, str(exc))
    return Success(manifest.model_dump())


@method
def get_workspace_capabilities(workspace_path: str) -> Success | Error:
    try:
        manifest = load_workspace(Path(workspace_path))
    except WorkspaceError as exc:
        return Error(-32602, str(exc))

    payload = capabilities_payload(manifest)
    check_capability(manifest, "max_assembly_parts", current_count=0)
    return Success(payload)


def _error_response(message: str) -> str:
    """Build a JSON-RPC error envelope for failures outside method dispatch."""
    return json.dumps(
        {
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32603, "message": message},
        }
    )


def process_request(line: str) -> str | None:
    """Dispatch one JSON-RPC line, converting any unexpected failure into an
    error response so a single bad request can never tear down the server loop."""
    try:
        return dispatch(line)
    except Exception as exc:  # noqa: BLE001 — keep the stdio loop alive at all costs
        return _error_response(f"Internal server error: {exc}")


def main() -> None:
    """Serve JSON-RPC requests line-by-line over stdio until stdin closes."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        response = process_request(line)
        if response:
            sys.stdout.write(response + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()