"""Unit tests for workspace manifest create/load (F-002)."""

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
    workspace = tmp_path / "my_project"
    manifest = create_workspace(workspace, "my_project")

    assert manifest.project_name == "my_project"
    assert manifest.edition == "community"
    assert manifest.capabilities == Capabilities()

    assert (workspace / "docs").is_dir()
    assert (workspace / "parts").is_dir()
    assert (workspace / "assemblies").is_dir()
    assert (workspace / "exports").is_dir()

    manifest_path = workspace / MANIFEST_FILENAME
    assert manifest_path.is_file()

    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert raw["project_name"] == "my_project"
    assert raw["edition"] == "community"
    assert raw["capabilities"]["max_assembly_parts"] == 5
    assert raw["capabilities"]["advanced_pdd"] is False


def test_load_workspace_returns_manifest(tmp_path: Path):
    workspace = tmp_path / "loaded_project"
    create_workspace(workspace, "loaded_project")

    loaded = load_workspace(workspace)
    assert isinstance(loaded, WorkspaceManifest)
    assert loaded.project_name == "loaded_project"
    assert loaded.edition == "community"


def test_load_workspace_missing_manifest_raises(tmp_path: Path):
    workspace = tmp_path / "empty"
    workspace.mkdir()

    with pytest.raises(WorkspaceNotFoundError, match="Missing workspace manifest"):
        load_workspace(workspace)


def test_load_workspace_invalid_json_raises(tmp_path: Path):
    workspace = tmp_path / "bad_json"
    workspace.mkdir()
    (workspace / MANIFEST_FILENAME).write_text("{not json", encoding="utf-8")

    with pytest.raises(WorkspaceInvalidError, match="Invalid JSON"):
        load_workspace(workspace)


def test_load_workspace_invalid_schema_raises(tmp_path: Path):
    workspace = tmp_path / "bad_schema"
    workspace.mkdir()
    (workspace / MANIFEST_FILENAME).write_text(
        json.dumps({"version": "0.1"}),
        encoding="utf-8",
    )

    with pytest.raises(WorkspaceInvalidError, match="Invalid workspace manifest"):
        load_workspace(workspace)
