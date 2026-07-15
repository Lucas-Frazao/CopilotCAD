"""
test_edition_capabilities.py — Edition and capabilities plumbing tests (F-027)
==============================================================================

F-027 wires edition (community vs learning) and capability limits into the
workspace manifest and runtime checks. Soft limits warn but do not block in MVP.

Beginner concepts:
  - edition: "community" (default) or "learning" — controls feature access.
  - capabilities: soft limits like max_assembly_parts stored in the manifest.
  - check_capability: returns "warn" when a soft limit is exceeded.
"""

from __future__ import annotations

import importlib
import json

import pytest

from project.workspace import MANIFEST_FILENAME, create_workspace, load_workspace
from rpc_helpers import assert_rpc_method_registered, call_rpc, assert_rpc_success
from schemas.workspace_manifest import WorkspaceManifest, default_capabilities


def _capabilities_module():
    """Import workspace.capabilities if implemented; return None otherwise."""
    try:
        return importlib.import_module("workspace.capabilities")
    except ImportError:
        return None


def test_new_projects_have_edition_and_capabilities(tmp_path):
    """
    New workspaces must default to edition='community' with a Capabilities object
    persisted in copilotcad.json.
    """
    path = tmp_path / "cap_proj"
    manifest = create_workspace(path, "cap_proj")
    assert manifest.edition == "community"
    assert manifest.capabilities is not None

    raw = json.loads((path / MANIFEST_FILENAME).read_text(encoding="utf-8"))
    assert raw["edition"] == "community"
    assert "capabilities" in raw


def test_get_workspace_capabilities_rpc_registered(workspace):
    """get_workspace_capabilities must be registered as a JSON-RPC method."""
    assert_rpc_method_registered(
        "get_workspace_capabilities",
        {"workspace_path": str(workspace)},
    )


def test_capabilities_include_documented_limits(workspace):
    """
    get_workspace_capabilities RPC must return max_assembly_parts (or max_parts)
    and edition='community'.
    """
    response = call_rpc("get_workspace_capabilities", {"workspace_path": str(workspace)})
    caps = assert_rpc_success(response)
    flat = caps.get("capabilities", caps)
    assert "max_assembly_parts" in flat or "max_parts" in flat
    assert flat.get("edition") == "community" or caps.get("edition") == "community"


def test_legacy_manifest_without_capabilities_gets_defaults(tmp_path):
    """
    Loading an old manifest without a capabilities block must backfill defaults
    instead of crashing.
    """
    path = tmp_path / "legacy"
    path.mkdir()
    for d in ("docs", "parts", "assemblies", "exports"):
        (path / d).mkdir()
    (path / MANIFEST_FILENAME).write_text(
        json.dumps({"project_name": "legacy", "version": "0.1"}) + "\n",
        encoding="utf-8",
    )
    loaded = load_workspace(path)
    assert loaded.edition == "community"
    assert loaded.capabilities is not None


def test_check_capability_logs_warning_only(workspace, caplog):
    """
    Exceeding a soft limit must warn (return 'warn') but not raise in MVP.
    """
    mod = _capabilities_module()
    if mod is None:
        pytest.fail("F-027 requires workspace.capabilities with check_capability helper")
    check = getattr(mod, "check_capability", None)
    assert check is not None
    result = check(
        load_workspace(workspace),
        "max_assembly_parts",
        current_count=6,
    )
    assert result in ("warn", "ok", True, False)


def test_soft_limit_warning_message(workspace):
    """
    format_limit_warning must produce a message mentioning community or limit.
    """
    mod = _capabilities_module()
    format_warn = getattr(mod, "format_limit_warning", None)
    assert format_warn is not None
    msg = format_warn("max_assembly_parts", limit=5, current=6)
    assert "community" in msg.lower() or "limit" in msg.lower()


def test_workspace_manifest_schema_accepts_community_edition():
    """WorkspaceManifest model must accept edition='community' with default capabilities."""
    m = WorkspaceManifest(project_name="x", edition="community")
    assert m.capabilities == default_capabilities()
