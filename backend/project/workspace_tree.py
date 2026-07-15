"""
Workspace File Tree — Explorer List + Safe Read (F-009)
=======================================================

WHAT THIS FILE DOES
-------------------
Powers the file explorer panel: nested tree of workspace folders and safe
read-only preview of text files over the JSON-RPC stdio bridge.

SECURITY
--------
``resolve_workspace_file`` blocks path traversal (..), absolute paths, and
reads outside the four allowed top-level dirs (WORKSPACE_DIRS).

SIZE LIMIT
----------
Preview reads cap at MAX_FILE_BYTES (1 MiB) to protect memory and IPC payload size.
"""

from __future__ import annotations

from pathlib import Path, PurePosixPath

from project.workspace import WORKSPACE_DIRS, WorkspaceError, load_workspace

MAX_FILE_BYTES = 1024 * 1024  # 1 MiB


class WorkspacePathError(WorkspaceError):
    """Raised when a relative path is invalid or escapes the workspace."""


def resolve_workspace_file(workspace: Path, relative_path: str) -> Path:
    """
    Resolve a workspace-relative path and ensure it stays inside the workspace.

    Rejects absolute paths (POSIX root, UNC, drive-letter), parent-directory
    traversal, and any path whose first segment is not one of WORKSPACE_DIRS.
    The final relative_to check also catches symlink escapes via .resolve().
    """
    if not relative_path or not relative_path.strip():
        raise WorkspacePathError("Relative path is required")

    # Check raw string before normalizing — prevents "/etc/passwd" style tricks
    raw = relative_path.replace("\\", "/")
    if raw.startswith("/"):
        raise WorkspacePathError("Absolute paths are not allowed")
    if len(raw) >= 2 and raw[1] == ":":
        raise WorkspacePathError("Absolute paths are not allowed")

    parts = PurePosixPath(raw.lstrip("/")).parts
    if not parts:
        raise WorkspacePathError("Relative path is required")
    if ".." in parts:
        raise WorkspacePathError("Path escapes workspace")
    if parts[0] not in WORKSPACE_DIRS:
        allowed = ", ".join(WORKSPACE_DIRS)
        raise WorkspacePathError(f"Reads are restricted to: {allowed}")

    workspace_root = workspace.resolve()
    target = (workspace_root / Path(*parts)).resolve()

    try:
        target.relative_to(workspace_root)
    except ValueError as exc:
        raise WorkspacePathError("Path escapes workspace") from exc

    return target


def _build_node(path: Path, workspace: Path, relative_path: str) -> dict:
    """Recursively build {name, path, type, children?} tree nodes."""
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
    """
    Read UTF-8 text from a file inside the workspace for read-only preview.

    Raises WorkspacePathError for missing, oversized, or non-UTF-8 files.
    """
    load_workspace(workspace)
    target = resolve_workspace_file(workspace, relative_path)

    if not target.is_file():
        raise WorkspacePathError(f"File not found: {relative_path}")

    size = target.stat().st_size
    if size > MAX_FILE_BYTES:
        raise WorkspacePathError(
            f"File too large to preview ({size} bytes; limit {MAX_FILE_BYTES})"
        )

    try:
        return target.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise WorkspacePathError(
            f"File is not valid UTF-8 text: {relative_path}"
        ) from exc
