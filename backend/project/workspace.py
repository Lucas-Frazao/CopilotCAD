"""
Workspace Root — copilotcad.json Manifest (F-009 base)
======================================================

WHAT THIS FILE DOES
-------------------
Creates and loads a CopilotCAD project folder. The manifest file
``copilotcad.json`` stores project name, edition, and capability limits.

STANDARD DIRECTORIES
--------------------
docs/, parts/, assemblies/, exports/ — created on workspace init.

EXCEPTIONS
----------
- WorkspaceNotFoundError — path missing or no manifest
- WorkspaceInvalidError — JSON parse or Pydantic validation failure
"""

import json
from pathlib import Path

from pydantic import ValidationError

from schemas.workspace_manifest import WorkspaceManifest, default_capabilities

MANIFEST_FILENAME = "copilotcad.json"
WORKSPACE_DIRS = ("docs", "parts", "assemblies", "exports")


class WorkspaceError(Exception):
    """Base error for workspace operations."""


class WorkspaceNotFoundError(WorkspaceError):
    """Raised when copilotcad.json is missing or the path is not a workspace."""


class WorkspaceInvalidError(WorkspaceError):
    """Raised when copilotcad.json exists but is invalid."""


def _manifest_path(workspace: Path) -> Path:
    return workspace / MANIFEST_FILENAME


def create_workspace(path: Path, project_name: str) -> WorkspaceManifest:
    """Create a new workspace folder with default manifest and directory layout."""
    path.mkdir(parents=True, exist_ok=True)

    for dirname in WORKSPACE_DIRS:
        (path / dirname).mkdir(exist_ok=True)

    manifest = WorkspaceManifest(
        project_name=project_name,
        edition="community",
        capabilities=default_capabilities(),
    )

    manifest_path = _manifest_path(path)
    manifest_path.write_text(
        json.dumps(manifest.model_dump(), indent=2) + "\n",
        encoding="utf-8",
    )

    return manifest


def load_workspace(path: Path) -> WorkspaceManifest:
    """Load and validate copilotcad.json from an existing workspace."""
    if not path.is_dir():
        raise WorkspaceNotFoundError(f"Workspace path does not exist: {path}")

    manifest_path = _manifest_path(path)
    if not manifest_path.is_file():
        raise WorkspaceNotFoundError(
            f"Missing workspace manifest: {manifest_path}"
        )

    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise WorkspaceInvalidError(
            f"Invalid JSON in workspace manifest: {manifest_path}"
        ) from exc

    try:
        return WorkspaceManifest.model_validate(raw)
    except ValidationError as exc:
        raise WorkspaceInvalidError(
            f"Invalid workspace manifest: {manifest_path} — {exc}"
        ) from exc
