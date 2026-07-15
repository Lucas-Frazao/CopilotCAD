"""
test_workspace_manifest.py — Workspace manifest create/load tests (F-002)
=========================================================================

Every CopilotCAD project has a copilotcad.json manifest at its root. It records
the project name, edition (community vs learning), and capability limits.

F-002 defines workspace creation. These tests verify manifest writing, folder
scaffolding, and error handling for corrupt or missing manifests.

Beginner concepts:
  - Manifest: copilotcad.json — the project's identity card on disk.
  - Capabilities: soft limits (max parts, advanced PDD, etc.) for each edition.
"""

import json
from pathlib import Path

import pytest

from project.workspace import (
    MANIFEST_FILENAME,
    WorkspaceInvalidError,
    WorkspaceManifest,
    WorkspaceNotFoundError,
    create_workspace,
    load_workspace,
)
from schemas.workspace_manifest import Capabilities


def test_create_workspace_writes_manifest_and_dirs(tmp_path: Path):
    """create_workspace must write the manifest and four standard subfolders."""
    workspace = tmp_path / "my_project"
    manifest = create_workspace(workspace, "my_project")

    # In-memory manifest object has expected defaults
    assert manifest.project_name == "my_project"
    assert manifest.edition == "community"
    assert manifest.capabilities == Capabilities()

    # Standard workspace directories exist on disk
    assert (workspace / "docs").is_dir()
    assert (workspace / "parts").is_dir()
    assert (workspace / "assemblies").is_dir()
    assert (workspace / "exports").is_dir()

    manifest_path = workspace / MANIFEST_FILENAME
    assert manifest_path.is_file()

    # Round-trip: read the JSON file and check key fields
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert raw["project_name"] == "my_project"
    assert raw["edition"] == "community"
    assert raw["capabilities"]["max_assembly_parts"] == 5
    assert raw["capabilities"]["advanced_pdd"] is False


def test_load_workspace_returns_manifest(tmp_path: Path):
    """load_workspace should parse an existing manifest back into a typed object."""
    workspace = tmp_path / "loaded_project"
    create_workspace(workspace, "loaded_project")

    loaded = load_workspace(workspace)
    assert isinstance(loaded, WorkspaceManifest)
    assert loaded.project_name == "loaded_project"
    assert loaded.edition == "community"


def test_load_workspace_missing_manifest_raises(tmp_path: Path):
    """An empty directory without copilotcad.json must raise WorkspaceNotFoundError."""
    workspace = tmp_path / "empty"
    workspace.mkdir()

    with pytest.raises(WorkspaceNotFoundError, match="Missing workspace manifest"):
        load_workspace(workspace)


def test_load_workspace_invalid_json_raises(tmp_path: Path):
    """Corrupt JSON in the manifest file must raise WorkspaceInvalidError."""
    workspace = tmp_path / "bad_json"
    workspace.mkdir()
    (workspace / MANIFEST_FILENAME).write_text("{not json", encoding="utf-8")

    with pytest.raises(WorkspaceInvalidError, match="Invalid JSON"):
        load_workspace(workspace)


def test_load_workspace_invalid_schema_raises(tmp_path: Path):
    """Valid JSON missing required fields must still fail schema validation."""
    workspace = tmp_path / "bad_schema"
    workspace.mkdir()
    (workspace / MANIFEST_FILENAME).write_text(
        json.dumps({"version": "0.1"}),
        encoding="utf-8",
    )

    with pytest.raises(WorkspaceInvalidError, match="Invalid workspace manifest"):
        load_workspace(workspace)
