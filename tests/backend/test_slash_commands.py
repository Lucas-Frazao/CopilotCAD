"""
test_slash_commands.py — Slash command handler tests (F-014)
==============================================================

Slash commands (/vision, /part, /export, etc.) let users scaffold project
artifacts from chat. F-014 defines handlers that create files under the workspace.

These tests verify each MVP command creates the expected artifact, bad args are
rejected, and /part scaffolds folders without writing geometry blobs.

Beginner concepts:
  - Slash command: chat message starting with / that triggers a backend handler.
  - handle_slash_command: parses the command string and writes scaffold files.
  - Parametrize: pytest runs one test function once per (command, meta) pair.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from project.workspace import create_workspace
from rpc_helpers import call_rpc, assert_rpc_success


def _slash_handler():
    """Import commands.slash_handlers.handle_slash_command or fail clearly."""
    try:
        mod = importlib.import_module("commands.slash_handlers")
    except ImportError as exc:
        pytest.fail(f"F-014 requires backend/commands/slash_handlers.py: {exc}")
    fn = getattr(mod, "handle_slash_command", None)
    assert fn is not None
    return fn


# MVP slash commands and the artifact file each one must create
MVP_COMMANDS: dict[str, dict] = {
    "/vision": {"path": "docs/product_vision.md"},
    "/constitution": {"path": "docs/constitution.md"},
    "/architecture": {"path": "docs/system_architecture.md"},
    "/manufacturing": {"path": "docs/manufacturing_stack.md"},
    "/part": {"path": "parts/test_part/spec.yaml", "args": "test_part"},
    "/interface": {"path": "parts/active_part/spec.yaml", "setup_part": "active_part"},
    "/plan": {"path": "parts/active_part/plan.md", "setup_part": "active_part"},
    "/review": {"path": "parts/active_part/review.md", "setup_part": "active_part"},
    "/release": {"path": "parts/active_part/spec.yaml", "setup_part": "active_part"},
    "/export": {"path": "exports/active_part.step", "setup_part": "active_part"},
    "/assumptions": {"path": "parts/active_part/assumptions.yaml", "setup_part": "active_part"},
    "/history": {"path": "parts/active_part/history.json", "setup_part": "active_part"},
}


@pytest.fixture
def slash_workspace(tmp_path: Path) -> Path:
    """Dedicated workspace fixture for slash command tests."""
    workspace = tmp_path / "slash_proj"
    create_workspace(workspace, "slash_proj")
    return workspace


@pytest.mark.parametrize("command,meta", list(MVP_COMMANDS.items()))
def test_slash_command_creates_expected_artifact(command, meta, slash_workspace):
    """
    Each MVP slash command must succeed and create its expected artifact file.

    pytest.mark.parametrize runs this test once per entry in MVP_COMMANDS.
    """
    handle = _slash_handler()
    context = {"workspace_path": str(slash_workspace), "active_part_id": "active_part"}

    # Some commands need a part folder scaffolded first
    if meta.get("setup_part"):
        from project.part_folder import create_part_folder

        create_part_folder(slash_workspace, meta["setup_part"])

    args = meta.get("args", "")
    full_command = f"{command} {args}".strip() if args else command
    result = handle(full_command, context)

    assert result.get("success") is True, result.get("error", result)
    target = slash_workspace / meta["path"]
    assert target.is_file(), f"{command} must create {meta['path']}"


def test_part_command_without_name_returns_error(slash_workspace):
    """'/part' with no part name must fail with a usage hint."""
    handle = _slash_handler()
    result = handle("/part", {"workspace_path": str(slash_workspace)})
    assert result.get("success") is False
    assert "usage" in result.get("error", "").lower() or "name" in result.get("error", "").lower()


def test_slash_command_jsonrpc_registered(slash_workspace):
    """handle_slash_command must be reachable via JSON-RPC."""
    from rpc_helpers import assert_rpc_method_registered

    assert_rpc_method_registered(
        "handle_slash_command",
        {"command": "/vision", "workspace_path": str(slash_workspace)},
    )


def test_slash_export_does_not_bypass_export_module(slash_workspace):
    """
    /part scaffolds YAML stub folders only — it must not embed geometry blobs.
    Real geometry export goes through the export module (F-024).
    """
    handle = _slash_handler()
    from project.part_folder import create_part_folder

    create_part_folder(slash_workspace, "plate")
    part_result = handle("/part new_widget", {"workspace_path": str(slash_workspace)})
    assert part_result.get("success") is True
    spec = slash_workspace / "parts" / "new_widget" / "spec.yaml"
    assert spec.is_file()
    assert "TopoDS" not in spec.read_text(encoding="utf-8")


def test_handle_slash_command_returns_chat_summary(slash_workspace):
    """Successful slash commands should return a summary or message for chat UI."""
    handle = _slash_handler()
    result = handle("/vision", {"workspace_path": str(slash_workspace)})
    assert "summary" in result or "message" in result
