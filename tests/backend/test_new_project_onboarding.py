"""
test_new_project_onboarding.py — New project onboarding tests (F-025)
====================================================================

F-025 defines chat-driven onboarding: create_workspace scaffolds a blank project
ready for the user's first chat message — no wizard UI, no onboarding state files.

Beginner concepts:
  - create_workspace: writes manifest + empty docs/parts/assemblies/exports folders.
  - Chat-driven onboarding: user types their first modeling request in chat.
  - WORKSPACE_DIRS: the four standard subdirectories every project gets.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from project.workspace import MANIFEST_FILENAME, WORKSPACE_DIRS, create_workspace, load_workspace
from rpc_helpers import assert_rpc_method_registered, call_rpc, assert_rpc_success


def test_create_workspace_rpc_registered(tmp_path):
    """create_workspace must be registered as a JSON-RPC method."""
    path = tmp_path / "new_proj"
    assert_rpc_method_registered(
        "create_workspace",
        {"path": str(path), "project_name": "My Project"},
    )


def test_create_workspace_makes_manifest_and_subfolders(tmp_path):
    """
    create_workspace must write copilotcad.json and all WORKSPACE_DIRS subfolders.
    """
    path = tmp_path / "new_proj"
    manifest = create_workspace(path, "My Project")

    assert (path / MANIFEST_FILENAME).is_file()
    for dirname in WORKSPACE_DIRS:
        assert (path / dirname).is_dir()

    loaded = load_workspace(path)
    assert loaded.project_name == "My Project"


def test_create_workspace_jsonrpc(tmp_path):
    """create_workspace RPC should succeed and write the manifest file."""
    path = tmp_path / "rpc_proj"
    response = call_rpc(
        "create_workspace",
        {"path": str(path), "project_name": "RPC Project"},
    )
    result = assert_rpc_success(response)
    assert result.get("project_name") == "RPC Project" or (path / MANIFEST_FILENAME).is_file()


def test_new_workspace_is_blank_ready_for_chat(tmp_path):
    """
    A freshly created workspace must have an empty parts/ folder and
    edition='community' in the manifest — ready for the first chat message.
    """
    path = tmp_path / "blank"
    create_workspace(path, "blank")

    parts = list((path / "parts").iterdir())
    assert parts == []
    raw = json.loads((path / MANIFEST_FILENAME).read_text(encoding="utf-8"))
    assert raw.get("edition") == "community"


def test_no_wizard_artifacts_created(tmp_path):
    """
    F-025 uses chat-driven onboarding — no wizard state files must be created.
    """
    path = tmp_path / "onboard"
    create_workspace(path, "onboard")
    wizard_markers = list(path.glob("**/*wizard*")) + list(path.glob("**/*onboarding*.json"))
    assert wizard_markers == []


def test_user_can_create_first_part_via_execute_after_onboarding(tmp_path, mounting_plate_ir_dict):
    """
    After onboarding, execute_intent with the golden plate IR must succeed,
    creating the user's first part via chat (requires OCCT).
    """
    pytest.importorskip("OCC.Core.TopoDS")
    path = tmp_path / "first_part"
    create_workspace(path, "first_part")

    response = call_rpc(
        "execute_intent",
        {
            "ir": mounting_plate_ir_dict,
            "workspace_path": str(path),
        },
    )
    payload = response.get("result") or response.get("error", {}).get("data", {})
    if not payload.get("success"):
        pytest.fail("New project must support first part via chat execute")
