# =============================================================================
# User-Facing Error Catalog (Feature F-026)
# =============================================================================
#
# WHAT THIS FILE DOES
# -------------------
# When something goes wrong (LLM parse failure, bad dimensions, export with
# no geometry, etc.), the UI needs friendly messages — not raw Python tracebacks.
#
# ERROR_CATALOG maps internal "mode IDs" (like compile_parse) to:
#   - error_type  — category for icons / filtering
#   - message     — short explanation for the user
#   - suggested_next_steps — actionable bullets in the Problems panel
#
# get_user_message() and format_error() turn exceptions into that shape.
# =============================================================================

from __future__ import annotations

from typing import Any

# CompileError carries parse/validation details from the IR compiler pipeline
from ir.compiler import CompileError

# -----------------------------------------------------------------------------
# Master lookup table — add a new entry when you introduce a new failure mode
# -----------------------------------------------------------------------------

ERROR_CATALOG: dict[str, dict[str, Any]] = {
    "compile_parse": {
        "error_type": "parse",
        "message": "Couldn't parse the modeling plan — try rephrasing with clear dimensions.",
        "suggested_next_steps": [
            "Rephrase your request with explicit mm dimensions.",
            "Ask for a single part at a time.",
        ],
    },
    "compile_validation": {
        "error_type": "validation",
        "message": "The modeling plan failed validation — check dimensions and step parameters.",
        "suggested_next_steps": [
            "Include length, width, and thickness in your prompt.",
            "Confirm the part name and summary are present.",
        ],
    },
    "execute_missing_param": {
        "error_type": "execution",
        "message": "A modeling step is missing a required parameter.",
        "suggested_next_steps": [
            "Review the failed step in the Problems panel.",
            "Re-run with corrected dimensions or parameters.",
        ],
    },
    "execute_kernel": {
        "error_type": "geometry",
        "message": "Geometry generation failed in the CAD kernel.",
        "suggested_next_steps": [
            "Check that dimensions are positive and physically plausible.",
            "Simplify the request and add features incrementally.",
        ],
    },
    "export_no_geometry": {
        "error_type": "export",
        "message": "No geometry is available to export — model this part first.",
        "suggested_next_steps": [
            "Run execute on a part_create intent in chat.",
            "Confirm the part folder has geometry.step cached.",
        ],
    },
    "slash_bad_args": {
        "error_type": "slash",
        "message": "Slash command usage is incorrect.",
        "suggested_next_steps": [
            "Check command syntax, e.g. /part <name>.",
            "Pick a command from the slash picker.",
        ],
    },
    "ipc_backend_down": {
        "error_type": "ipc",
        "message": "Backend is not responding — restart the CopilotCAD app.",
        "suggested_next_steps": [
            "Restart the desktop app.",
            "Check that the Python backend process is running.",
        ],
    },
    "config_no_api_key": {
        "error_type": "configuration",
        "message": "LLM is not configured — set ANTHROPIC_API_KEY.",
        "suggested_next_steps": [
            "Export ANTHROPIC_API_KEY in your environment.",
            "Restart the backend after setting the key.",
        ],
    },
    "approval_rejected": {
        "error_type": "approval",
        "message": "High-risk action was rejected and not executed.",
        "suggested_next_steps": [
            "Review the pending action details.",
            "Re-submit with a safer alternative if needed.",
        ],
    },
    "workspace_invalid": {
        "error_type": "workspace",
        "message": "Workspace path is missing or invalid.",
        "suggested_next_steps": [
            "Create a workspace with create_workspace.",
            "Open an existing project folder.",
        ],
    },
    "assembly_limit": {
        "error_type": "capabilities",
        "message": "Assembly instance limit reached for this edition.",
        "suggested_next_steps": [
            "Reduce the number of instances in the assembly.",
            "Upgrade edition for higher limits.",
        ],
    },
}


def get_user_message(mode_id: str, *, error_type: str | None = None, details: Any = None) -> str:
    """
    Look up a catalog message by mode_id, with small special cases.

    mode_id examples: "compile_parse", "execute_kernel", "workspace_invalid"
    """
    entry = ERROR_CATALOG.get(mode_id, {})
    message = entry.get("message", f"An error occurred ({mode_id}).")

    # Validation errors with field_errors get a slightly more specific hint
    if mode_id == "compile_validation":
        if isinstance(details, dict):
            field_errors = details.get("field_errors", [])
            if field_errors:
                return (
                    "The modeling plan failed validation — add missing fields and dimensions."
                )
        return "The modeling plan failed validation — check dimensions and summary."

    if error_type and error_type in {entry.get("error_type"), mode_id}:
        return str(message)
    return str(message)


def format_error(err: Any) -> dict[str, Any]:
    """
    Normalize any error object into the UI-friendly dict shape.

    Handles CompileError, generic Exception, or a bare mode_id string.
    """
    # Structured compile failures from ir.compiler
    if isinstance(err, CompileError):
        mode_id = f"compile_{err.error_type}"
        entry = ERROR_CATALOG.get(mode_id, {})
        return {
            "error_type": err.error_type,
            "message": err.message,
            "details": err.details,
            "suggested_next_steps": entry.get("suggested_next_steps", []),
        }

    # Generic Python exceptions — guess category from message text
    if isinstance(err, Exception):
        message = str(err)
        mode_id = "execute_kernel"
        if "geometry" in message.lower() or "export" in message.lower():
            mode_id = "export_no_geometry" if "export" in message.lower() else "execute_kernel"
        entry = ERROR_CATALOG.get(mode_id, {})
        return {
            "error_type": entry.get("error_type", "unknown"),
            "message": get_user_message(mode_id),
            "details": {"raw": message},
            "suggested_next_steps": entry.get("suggested_next_steps", []),
        }

    # Fallback: treat err as a catalog key string
    entry = ERROR_CATALOG.get(str(err), {})
    return {
        "error_type": entry.get("error_type", "unknown"),
        "message": get_user_message(str(err)),
        "suggested_next_steps": entry.get("suggested_next_steps", []),
    }
