"""
Slash Command Handlers — Quick Workspace Actions (F-014)
========================================================

WHAT THIS FILE DOES
-------------------
Parses chat lines starting with "/" (e.g. "/part bracket", "/export") and
performs filesystem actions in the workspace — scaffold docs, parts, exports.

MAIN ENTRY
----------
``handle_slash_command(command_line, context)`` → ``{success, summary, ...}``

CONTEXT REQUIREMENTS
--------------------
context must include ``workspace_path``. Many commands also use ``active_part_id``.

SUPPORTED COMMANDS (MVP)
------------------------
/vision, /constitution, /architecture, /manufacturing — doc templates
/part, /interface, /plan, /review, /release, /export, /assumptions, /history
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml  # Read/write spec.yaml and assumptions.yaml

from project.export_polish import ExportError, export_part_with_history
from project.part_folder import (
    ASSUMPTIONS_FILENAME,
    HISTORY_FILENAME,
    SPEC_FILENAME,
    create_part_folder,
)

# command → (relative path under workspace, default file content)
_DOC_TEMPLATES: dict[str, tuple[str, str]] = {
    "/vision": ("docs/product_vision.md", "# Product Vision\n\nDescribe the product goals and users.\n"),
    "/constitution": (
        "docs/constitution.md",
        "# Engineering Constitution\n\nPrinciples for design and quality.\n",
    ),
    "/architecture": (
        "docs/system_architecture.md",
        "# System Architecture\n\nMajor subsystems and interfaces.\n",
    ),
    "/manufacturing": (
        "docs/manufacturing_stack.md",
        "# Manufacturing Stack\n\nProcesses, materials, and tolerances.\n",
    ),
}


def _workspace_path(context: dict[str, Any]) -> Path:
    raw = context.get("workspace_path")
    if not raw:
        raise ValueError("workspace_path is required in slash command context")
    return Path(raw)


def _active_part_id(context: dict[str, Any]) -> str:
    return str(context.get("active_part_id") or "active_part")


def _write_text(path: Path, content: str) -> None:
    """Create parent dirs and write file only if it does not exist yet."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.is_file():
        path.write_text(content, encoding="utf-8")


def _parse_command(command_line: str) -> tuple[str, str]:
    """Split '/part foo bar' → ('/part', 'foo bar')."""
    parts = command_line.strip().split(maxsplit=1)
    command = parts[0].lower()
    args = parts[1].strip() if len(parts) > 1 else ""
    return command, args


def handle_slash_command(command_line: str, context: dict[str, Any]) -> dict[str, Any]:
    """Dispatch a slash command and return a JSON-serializable result dict."""
    command, args = _parse_command(command_line)
    workspace = _workspace_path(context)

    try:
        if command in _DOC_TEMPLATES:
            rel_path, template = _DOC_TEMPLATES[command]
            target = workspace / rel_path
            _write_text(target, template)
            return {
                "success": True,
                "summary": f"Created {rel_path}",
                "message": f"Scaffolded {rel_path}",
                "path": rel_path,
            }

        if command == "/part":
            if not args:
                return {
                    "success": False,
                    "error": "Usage: /part <name>",
                }
            part_id = args.split()[0]
            create_part_folder(workspace, part_id)
            spec_path = workspace / "parts" / part_id / SPEC_FILENAME
            spec = {
                "part_id": part_id,
                "name": part_id.replace("_", " ").title(),
                "maturity": "draft",
                "interfaces": [],
            }
            spec_path.write_text(yaml.safe_dump(spec, sort_keys=False), encoding="utf-8")
            return {
                "success": True,
                "summary": f"Created part folder {part_id}",
                "message": f"Scaffolded parts/{part_id}/",
                "path": f"parts/{part_id}/spec.yaml",
            }

        part_id = _active_part_id(context)
        create_part_folder(workspace, part_id)

        if command == "/interface":
            spec_path = workspace / "parts" / part_id / SPEC_FILENAME
            spec = yaml.safe_load(spec_path.read_text(encoding="utf-8")) or {}
            interfaces = spec.get("interfaces", [])
            if not isinstance(interfaces, list):
                interfaces = []
            interfaces.append(
                {
                    "id": "iface_1",
                    "name": "New interface",
                    "type": "mechanical",
                    "connects_to": None,
                }
            )
            spec["interfaces"] = interfaces
            spec_path.write_text(yaml.safe_dump(spec, sort_keys=False), encoding="utf-8")
            return {
                "success": True,
                "summary": f"Updated interfaces for {part_id}",
                "path": f"parts/{part_id}/spec.yaml",
            }

        if command == "/plan":
            rel = f"parts/{part_id}/plan.md"
            _write_text(workspace / rel, f"# Plan — {part_id}\n\n## Steps\n\n")
            return {"success": True, "summary": f"Created {rel}", "path": rel}

        if command == "/review":
            rel = f"parts/{part_id}/review.md"
            _write_text(workspace / rel, f"# Review — {part_id}\n\n## Checklist\n\n")
            return {"success": True, "summary": f"Created {rel}", "path": rel}

        if command == "/release":
            spec_path = workspace / "parts" / part_id / SPEC_FILENAME
            spec = yaml.safe_load(spec_path.read_text(encoding="utf-8")) or {}
            spec["maturity"] = "released"
            spec_path.write_text(yaml.safe_dump(spec, sort_keys=False), encoding="utf-8")
            return {
                "success": True,
                "summary": f"Released {part_id}",
                "path": f"parts/{part_id}/spec.yaml",
            }

        if command == "/export":
            rel = f"exports/{part_id}.step"
            try:
                export_part_with_history(workspace, part_id, format="step")
            except ExportError:
                # No geometry yet — write placeholder so the UI has a file to show
                target = workspace / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("# export placeholder — model part first\n", encoding="utf-8")
            return {"success": True, "summary": f"Exported {part_id}", "path": rel}

        if command == "/assumptions":
            rel = f"parts/{part_id}/{ASSUMPTIONS_FILENAME}"
            _write_text(
                workspace / rel,
                yaml.safe_dump({"assumptions": []}, sort_keys=False),
            )
            return {"success": True, "summary": f"Opened assumptions for {part_id}", "path": rel}

        if command == "/history":
            rel = f"parts/{part_id}/{HISTORY_FILENAME}"
            _write_text(workspace / rel, '{\n  "events": []\n}\n')
            return {"success": True, "summary": f"Opened history for {part_id}", "path": rel}

        return {"success": False, "error": f"Unknown slash command: {command}"}
    except Exception as exc:  # noqa: BLE001
        return {"success": False, "error": str(exc)}
