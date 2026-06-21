"""Workspace file tree listing and safe read for explorer (F-009)."""

from __future__ import annotations

from pathlib import Path, PurePosixPath

from project.workspace import WORKSPACE_DIRS, WorkspaceError, load_workspace

# Preview reads are capped so a single large file (e.g. a multi-MB STEP export)
# cannot be slurped fully into memory and pushed over the stdio bridge.
MAX_FILE_BYTES = 1024 * 1024  # 1 MiB


class WorkspacePathError(WorkspaceError):
    """Raised when a relative path is invalid or escapes the workspace."""


def resolve_workspace_file(workspace: Path, relative_path: str) -> Path:
    """Resolve a workspace-relative path and ensure it stays inside the workspace.

    Rejects absolute paths (POSIX root, UNC, and drive-letter), parent-directory
    traversal, and any path whose first segment is not one of ``WORKSPACE_DIRS``.
    The final ``relative_to`` check is defence-in-depth that also catches symlink
    escapes (``.resolve()`` follows links). Returns the absolute target path.
    """
    if not relative_path or not relative_path.strip():
        raise WorkspacePathError("Relative path is required")

    # Inspect the raw form *before* stripping so absolute/UNC inputs are rejected
    # rather than silently coerced into a workspace-relative path.
    raw = relative_path.replace("\\", "/")
    if raw.startswith("/"):  # POSIX root "/etc" or UNC "//server/share"
        raise WorkspacePathError("Absolute paths are not allowed")
    if len(raw) >= 2 and raw[1] == ":":  # drive-letter "C:/..."
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
    """Read UTF-8 text from a file inside the workspace for read-only preview.

    Validates the path via :func:`resolve_workspace_file`, then rejects files that
    exceed ``MAX_FILE_BYTES`` or are not valid UTF-8 text. Raises
    :class:`WorkspacePathError` for a missing/oversized/binary file so callers can
    surface a structured error instead of an unhandled ``UnicodeDecodeError``.
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
