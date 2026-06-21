"""Workspace file tree listing and safe read for explorer (F-009)."""

from __future__ import annotations

from pathlib import Path, PurePosixPath

from project.workspace import WORKSPACE_DIRS, WorkspaceError, load_workspace


class WorkspacePathError(WorkspaceError):
    """Raised when a relative path is invalid or escapes the workspace."""


def _normalize_relative_path(relative_path: str) -> str:
    return relative_path.replace("\\", "/").lstrip("/")


def resolve_workspace_file(workspace: Path, relative_path: str) -> Path:
    """Resolve a workspace-relative path and ensure it stays inside the workspace."""
    if not relative_path or not relative_path.strip():
        raise WorkspacePathError("Relative path is required")

    normalized = _normalize_relative_path(relative_path)
    if normalized.startswith("/"):
        raise WorkspacePathError("Absolute paths are not allowed")

    if len(normalized) > 1 and normalized[1] == ":":
        raise WorkspacePathError("Absolute paths are not allowed")

    parts = PurePosixPath(normalized).parts
    if ".." in parts:
        raise WorkspacePathError("Path escapes workspace")

    workspace_root = workspace.resolve()
    target = (workspace_root / Path(*parts)).resolve()

    try:
        target.relative_to(workspace_root)
    except ValueError as exc:
        raise WorkspacePathError("Path escapes workspace") from exc

    return target


def _build_node(path: Path, workspace: Path, relative_path: str) -> dict:
    if path.is_dir():
        children: list[dict] = []
        try:
            entries = sorted(
                path.iterdir(),
                key=lambda entry: (not entry.is_dir(), entry.name.lower()),
            )
        except OSError:
            entries = []

        for entry in entries:
            child_relative = f"{relative_path}/{entry.name}"
            children.append(_build_node(entry, workspace, child_relative))

        return {
            "name": path.name,
            "path": relative_path,
            "type": "dir",
            "children": children,
        }

    return {
        "name": path.name,
        "path": relative_path,
        "type": "file",
    }


def list_workspace_tree(workspace: Path) -> list[dict]:
    """Return nested tree nodes for standard workspace directories."""
    load_workspace(workspace)

    nodes: list[dict] = []
    for dirname in WORKSPACE_DIRS:
        dir_path = workspace / dirname
        if dir_path.is_dir():
            nodes.append(_build_node(dir_path, workspace, dirname))

    return nodes


def read_workspace_file(workspace: Path, relative_path: str) -> str:
    """Read UTF-8 text from a file inside the workspace."""
    load_workspace(workspace)
    target = resolve_workspace_file(workspace, relative_path)

    if not target.is_file():
        raise WorkspacePathError(f"File not found: {relative_path}")

    return target.read_text(encoding="utf-8")
