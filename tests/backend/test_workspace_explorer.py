"""
test_workspace_explorer.py — Workspace explorer tree and file read tests (F-009)
================================================================================

The workspace explorer lets the frontend browse project files as a tree and
read text contents safely. These tests verify tree listing, file reads, path
sandboxing (no directory traversal), and JSON-RPC endpoints.

F-009 defines list_workspace_tree and read_workspace_file.

Beginner concepts:
  - Workspace tree: nested dict nodes with name, path, type (dir/file), children.
  - WorkspacePathError: raised when a path escapes the workspace or hits guards.
  - dispatch: routes JSON-RPC calls without starting a separate server.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonrpcserver import dispatch

from project.part_folder import (
    ASSUMPTIONS_FILENAME,
    HISTORY_FILENAME,
    SPEC_FILENAME,
    create_part_folder,
)
from project.workspace import create_workspace
from project.workspace_tree import (
    WorkspacePathError,
    list_workspace_tree,
    read_workspace_file,
)


def _node_names(nodes: list[dict]) -> set[str]:
    """Extract the 'name' field from a list of tree nodes."""
    return {node["name"] for node in nodes}


def _find_node(nodes: list[dict], path: str) -> dict | None:
    """Recursively search the tree for a node with the given relative path."""
    for node in nodes:
        if node["path"] == path:
            return node
        children = node.get("children") or []
        found = _find_node(children, path)
        if found is not None:
            return found
    return None


def test_list_workspace_tree_returns_top_level_dirs(tmp_path: Path):
    """A new workspace tree should expose docs, parts, assemblies, exports."""
    workspace = tmp_path / "proj"
    create_workspace(workspace, "proj")

    tree = list_workspace_tree(workspace)
    assert _node_names(tree) == {"docs", "parts", "assemblies", "exports"}
    for node in tree:
        assert node["type"] == "dir"
        assert node["path"] in {"docs", "parts", "assemblies", "exports"}


def test_list_workspace_tree_includes_part_artifacts(tmp_path: Path):
    """Creating a part should make its artifact files visible in the tree."""
    workspace = tmp_path / "proj"
    create_workspace(workspace, "proj")
    create_part_folder(workspace, "mounting_plate")

    tree = list_workspace_tree(workspace)
    part_dir = _find_node(tree, "parts/mounting_plate")
    assert part_dir is not None
    assert part_dir["type"] == "dir"

    artifact_names = _node_names(part_dir.get("children") or [])
    assert {SPEC_FILENAME, ASSUMPTIONS_FILENAME, HISTORY_FILENAME}.issubset(
        artifact_names
    )


def test_list_workspace_tree_jsonrpc(tmp_path: Path):
    """list_workspace_tree RPC should return the same tree structure as the direct call."""
    workspace = tmp_path / "proj"
    create_workspace(workspace, "proj")
    create_part_folder(workspace, "mounting_plate")

    request = json.dumps(
        {
            "jsonrpc": "2.0",
            "method": "list_workspace_tree",
            "params": {"workspace_path": str(workspace)},
            "id": 1,
        }
    )
    response = json.loads(dispatch(request))

    assert "result" in response
    tree = response["result"]
    assert _node_names(tree) == {"docs", "parts", "assemblies", "exports"}
    part_dir = _find_node(tree, "parts/mounting_plate")
    assert part_dir is not None


def test_read_workspace_file_returns_text(tmp_path: Path):
    """read_workspace_file should return the spec.yaml contents as a string."""
    workspace = tmp_path / "proj"
    create_workspace(workspace, "proj")
    create_part_folder(workspace, "mounting_plate")

    contents = read_workspace_file(workspace, "parts/mounting_plate/spec.yaml")
    assert isinstance(contents, str)
    assert contents.strip() != ""


def test_read_workspace_file_jsonrpc(tmp_path: Path):
    """read_workspace_file RPC should wrap contents in a result object."""
    workspace = tmp_path / "proj"
    create_workspace(workspace, "proj")
    create_part_folder(workspace, "mounting_plate")

    request = json.dumps(
        {
            "jsonrpc": "2.0",
            "method": "read_workspace_file",
            "params": {
                "workspace_path": str(workspace),
                "relative_path": "parts/mounting_plate/spec.yaml",
            },
            "id": 2,
        }
    )
    response = json.loads(dispatch(request))

    assert "result" in response
    assert isinstance(response["result"]["contents"], str)


def test_read_workspace_file_rejects_path_outside_workspace(tmp_path: Path):
    """
    Path traversal (../outside.txt) and absolute paths must raise WorkspacePathError.
    This prevents the renderer from reading arbitrary files on disk.
    """
    workspace = tmp_path / "proj"
    create_workspace(workspace, "proj")
    outside = tmp_path / "outside.txt"
    outside.write_text("secret", encoding="utf-8")

    with pytest.raises(WorkspacePathError):
        read_workspace_file(workspace, "../outside.txt")

    with pytest.raises(WorkspacePathError):
        read_workspace_file(workspace, str(outside))


def test_read_workspace_file_rejects_missing_file(tmp_path: Path):
    """Reading a path that does not exist should raise WorkspacePathError."""
    workspace = tmp_path / "proj"
    create_workspace(workspace, "proj")

    with pytest.raises(WorkspacePathError):
        read_workspace_file(workspace, "parts/missing/spec.yaml")


def test_read_workspace_file_jsonrpc_rejects_escape(tmp_path: Path):
    """RPC layer should return an error (not crash) for path traversal attempts."""
    workspace = tmp_path / "proj"
    create_workspace(workspace, "proj")
    outside = tmp_path / "outside.txt"
    outside.write_text("secret", encoding="utf-8")

    request = json.dumps(
        {
            "jsonrpc": "2.0",
            "method": "read_workspace_file",
            "params": {
                "workspace_path": str(workspace),
                "relative_path": "../outside.txt",
            },
            "id": 3,
        }
    )
    response = json.loads(dispatch(request))

    assert "error" in response


def test_list_workspace_tree_invalid_workspace(tmp_path: Path):
    """A directory without a manifest should fail both direct call and RPC."""
    bad = tmp_path / "not_a_workspace"
    bad.mkdir()

    with pytest.raises(Exception):
        list_workspace_tree(bad)

    request = json.dumps(
        {
            "jsonrpc": "2.0",
            "method": "list_workspace_tree",
            "params": {"workspace_path": str(bad)},
            "id": 4,
        }
    )
    response = json.loads(dispatch(request))
    assert "error" in response
