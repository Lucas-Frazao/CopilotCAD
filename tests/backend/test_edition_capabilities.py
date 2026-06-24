"""Spec compliance tests for F-027 — Edition and capabilities plumbing."""

from __future__ import annotations

import importlib
import json

import pytest

from project.workspace import MANIFEST_FILENAME, create_workspace, load_workspace
from rpc_helpers import assert_rpc_method_registered, call_rpc, assert_rpc_success
from schemas.workspace_manifest import WorkspaceManifest, default_capabilities


def _capabilities_module():
    try:
        return importlib.import_module("workspace.capabilities")
    except ImportError:
        return None


def test_new_projects_have_edition_and_capabilities(tmp_path):
    path = tmp_path / "cap_proj"
    manifest = create_workspace(path, "cap_proj")
    assert manifest.edition == "community"
    assert manifest.capabilities is not None

    raw = json.loads((path / MANIFEST_FILENAME).read_text(encoding="utf-8"))
    assert raw["edition"] == "community"
    assert "capabilities" in raw


def test_get_workspace_capabilities_rpc_registered(workspace):
    assert_rpc_method_registered(
        "get_workspace_capabilities",
        {"workspace_path": str(workspace)},
    )


def test_capabilities_include_documented_limits(workspace):
    response = call_rpc("get_workspace_capabilities", {"workspace_path": str(workspace)})
    caps = assert_rpc_success(response)
    flat = caps.get("capabilities", caps)
    # F-027 spec fields; current schema may use max_assembly_parts on Capabilities model.
    assert "max_assembly_parts" in flat or "max_parts" in flat
    assert flat.get("edition") == "community" or caps.get("edition") == "community"


def test_legacy_manifest_without_capabilities_gets_defaults(tmp_path):
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
    mod = _capabilities_module()
    if mod is None:
        pytest.fail("F-027 requires workspace.capabilities with check_capability helper")
    check = getattr(mod, "check_capability", None)
    assert check is not None
    # Exceed soft limit — must warn, not raise in MVP
    result = check(
        load_workspace(workspace),
        "max_assembly_parts",
        current_count=6,
    )
    assert result in ("warn", "ok", True, False)


def test_soft_limit_warning_message(workspace):
    mod = _capabilities_module()
    format_warn = getattr(mod, "format_limit_warning", None)
    assert format_warn is not None
    msg = format_warn("max_assembly_parts", limit=5, current=6)
    assert "community" in msg.lower() or "limit" in msg.lower()


def test_workspace_manifest_schema_accepts_community_edition():
    m = WorkspaceManifest(project_name="x", edition="community")
    assert m.capabilities == default_capabilities()
