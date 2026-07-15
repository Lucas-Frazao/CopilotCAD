# =============================================================================
# CopilotCAD Backend — JSON-RPC Server Entry Point
# =============================================================================
#
# WHAT THIS FILE DOES
# -------------------
# This is the "brain" of the CopilotCAD desktop app. The Electron frontend
# (the UI you see) talks to this Python process over stdin/stdout using a
# protocol called JSON-RPC. Each line on stdin is one request; each line on
# stdout is one response.
#
# Think of it like a restaurant: the frontend is the waiter, this file is
# the kitchen, and each @method function is a dish the kitchen knows how to
# make (ping, compile_intent, export_part, etc.).
#
# HOW TO READ THIS FILE
# ---------------------
# 1. Imports — what other modules we depend on
# 2. Module-level state — shared objects (LLM adapter, pending approvals)
# 3. @method functions — the RPC "menu" the frontend can call
# 4. main() — the loop that reads requests forever until stdin closes
# =============================================================================

# Allow forward references in type hints (e.g. "ClaudeAdapter | None" before
# the class is fully defined). Safe on Python 3.7+.
from __future__ import annotations

# json — serialize/deserialize JSON-RPC responses
import json

# sys — access stdin/stdout for the RPC transport
import sys

# Path — turn string paths into rich path objects (cross-platform)
from pathlib import Path

# Any — "this value can be any JSON-serializable type"
from typing import Any

# jsonrpcserver — tiny library that wires @method decorators to dispatch()
from jsonrpcserver import Error, InvalidParams, Success, dispatch, method

# --- Approval flow (high-risk intents need user confirmation) ---
from approval.pending_store import PendingIntentStore, reject_pending
from approval.risk_classifier import classify_intent_risk

# --- Slash commands typed in chat (e.g. /part bracket) ---
from commands.slash_handlers import handle_slash_command as run_slash_command

# --- Core CAD execution: Intent IR → geometry on disk ---
from engine.executor import execute_intent_ir

# --- Compile pipeline: natural language → validated Intent IR ---
from ir.compiler import CompileError, compile_intent as run_compile_intent
from ir.validator import IntentIRValidationError, validate_intent_ir

# --- LLM (Claude) adapter for turning chat into structured JSON ---
from llm.claude_adapter import ClaudeAdapter
from llm.errors import LLMConfigurationError

# --- Problems engine: surfaces warnings/errors after execution ---
from problems.engine import evaluate_problems, problems_to_dicts

# --- Project data: assumptions, exports, geometry cache, history ---
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

# --- Edition limits (community vs pro caps) ---
from workspace.capabilities import capabilities_payload, check_capability

# Lazy singleton: we only construct ClaudeAdapter on first compile_intent call
# so startup stays fast and missing API keys don't crash ping().
_default_adapter: ClaudeAdapter | None = None

# In-memory store for intents awaiting user approval (high-risk actions)
_pending_store = PendingIntentStore()


def _get_claude_adapter() -> ClaudeAdapter:
    """Return the shared Claude adapter, creating it on first use."""
    global _default_adapter
    if _default_adapter is None:
        _default_adapter = ClaudeAdapter()
    return _default_adapter


# -----------------------------------------------------------------------------
# RPC Methods — each @method becomes callable from the frontend via JSON-RPC
# -----------------------------------------------------------------------------


@method
def ping() -> Success:
    """Health check. Frontend calls this to verify the backend is alive."""
    return Success("pong")


@method
def execute_intent(
    ir: dict[str, Any],
    workspace_path: str | None = None,
) -> Success | Error:
    """
    Run a validated Intent IR against the workspace (create/edit parts, etc.).

    Flow: validate → execute → evaluate problems → return payload or error.
    """
    # Step 1: Turn the raw dict into a typed IntentIR; reject bad shapes early
    try:
        intent = validate_intent_ir(ir)
    except IntentIRValidationError as exc:
        return InvalidParams(exc.to_dict())

    # Step 2: Run CAD steps (sketch, extrude, holes, …) via the executor
    result = execute_intent_ir(intent, workspace_path=workspace_path)

    # Step 3: Attach human-readable problems (missing dims, failed geometry, …)
    problems = evaluate_problems(intent, result)
    payload = result.to_dict()
    payload["problems"] = problems_to_dicts(problems)

    if not result.success:
        # JSON-RPC "internal error" with extra payload for the UI
        return Error(-32603, result.error or "Execution failed", payload)

    return Success(payload)


@method
def compile_intent(message: str, context: dict[str, Any] | None = None) -> Success | Error:
    """
    Turn a chat message into Intent IR using the LLM.

    May return a pending approval envelope instead of raw intent when risk is high.
    """
    # Imported here (not at top) to avoid circular imports and speed cold start
    from pdd.classifier import build_pdd_suggestion_payload, classify_request_complexity

    # Very complex requests get routed to Product Definition Document flow
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

    # High-risk intents (e.g. destructive edits) wait for explicit approval
    if classify_intent_risk(intent_dict) == "high":
        pending_id = _pending_store.add(intent_dict)
        return Success({"pending": True, "pending_id": pending_id, "intent": intent_dict})

    return Success(intent_dict)


@method
def list_workspace_tree(workspace_path: str) -> Success | Error:
    """Return the folder/file tree for a project workspace."""
    try:
        tree = build_workspace_tree(Path(workspace_path))
    except WorkspaceError as exc:
        return Error(-32602, str(exc))

    return Success(tree)


@method
def read_workspace_file(workspace_path: str, relative_path: str) -> Success | Error:
    """Read a text file inside the workspace (specs, docs, etc.)."""
    try:
        contents = read_workspace_text(Path(workspace_path), relative_path)
    except WorkspacePathError as exc:
        return Error(-32602, str(exc))
    except WorkspaceError as exc:
        return Error(-32602, str(exc))

    return Success({"contents": contents})


@method
def get_part_mesh(workspace_path: str, part_id: str) -> Success | Error:
    """Build a triangle mesh payload for 3D viewport rendering."""
    from mesh.part_mesh import build_part_mesh_payload

    shape = load_part_geometry(Path(workspace_path), part_id)
    if shape is None:
        return Error(-32602, f"No geometry for part '{part_id}'")
    return Success(build_part_mesh_payload(shape))


@method
def get_assembly_mesh(workspace_path: str, assembly_id: str) -> Success | Error:
    """Build a combined mesh for all instances in an assembly."""
    from mesh.assembly_mesh import build_assembly_mesh_payload

    try:
        payload = build_assembly_mesh_payload(Path(workspace_path), assembly_id)
    except Exception as exc:  # noqa: BLE001 — mesh build can fail many ways; always return RPC error
        return Error(-32602, str(exc))
    return Success(payload)


@method
def list_parts(workspace_path: str) -> Success | Error:
    """List all parts defined in the workspace."""
    return Success(build_parts_list(Path(workspace_path)))


@method
def list_interfaces(workspace_path: str) -> Success | Error:
    """List mating interfaces between parts."""
    return Success(build_interfaces_list(Path(workspace_path)))


@method
def get_part_history(workspace_path: str, part_id: str) -> Success | Error:
    """Return the step history / timeline for one part."""
    return Success(read_part_history(Path(workspace_path), part_id))


@method
def handle_slash_command(
    command: str,
    workspace_path: str,
    active_part_id: str | None = None,
) -> Success | Error:
    """Dispatch chat slash commands like /part or /export."""
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
    """Confirm, reject, or edit a design assumption on a part."""
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
    """Execute a previously stored high-risk intent after user approval."""
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
    """Discard a pending high-risk intent without executing it."""
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
    """Export one part to STEP (or another format) on disk."""
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
    """Export an entire assembly to STEP (or another format)."""
    try:
        path = export_assembly_file(Path(workspace_path), assembly_id, format=format)  # type: ignore[arg-type]
    except ExportError as exc:
        return Error(-32602, str(exc))
    return Success({"path": str(path)})


@method
def create_workspace(path: str, project_name: str) -> Success | Error:
    """Create a new on-disk project folder with manifest and default layout."""
    try:
        manifest = init_workspace(Path(path), project_name)
    except OSError as exc:
        return Error(-32603, str(exc))
    return Success(manifest.model_dump())


@method
def get_workspace_capabilities(workspace_path: str) -> Success | Error:
    """Return edition limits (max assembly parts, PDD, scripting, etc.)."""
    try:
        manifest = load_workspace(Path(workspace_path))
    except WorkspaceError as exc:
        return Error(-32602, str(exc))

    payload = capabilities_payload(manifest)
    # Side-effect check ensures capability logic stays exercised
    check_capability(manifest, "max_assembly_parts", current_count=0)
    return Success(payload)


# -----------------------------------------------------------------------------
# Server loop — one JSON object per line, never crash on a bad request
# -----------------------------------------------------------------------------


def _error_response(message: str) -> str:
    """
    Build a JSON-RPC error envelope for failures outside @method dispatch.

    Used when dispatch() itself throws — keeps the stdio loop alive.
    """
    return json.dumps(
        {
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32603, "message": message},
        }
    )


def process_request(line: str) -> str | None:
    """
    Dispatch one JSON-RPC line to the matching @method handler.

    Any unexpected exception becomes a JSON error response instead of
    killing the server — one bad request must not take down the whole app.
    """
    try:
        return dispatch(line)
    except Exception as exc:  # noqa: BLE001 — last-resort guard for the stdio loop
        return _error_response(f"Internal server error: {exc}")


def main() -> None:
    """
    Serve JSON-RPC requests line-by-line over stdio until stdin closes.

    Electron spawns this process and pipes requests/responses through pipes.
    """
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue  # ignore blank lines

        response = process_request(line)
        if response:
            sys.stdout.write(response + "\n")
            sys.stdout.flush()  # flush so Electron gets the reply immediately


# Standard Python entry: `python -m backend.main` or direct script run
if __name__ == "__main__":
    main()
