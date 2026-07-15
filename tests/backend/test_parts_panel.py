"""
test_parts_panel.py — Parts panel spec compliance tests (F-015)
================================================================

The Parts panel lists all parts in a workspace with maturity and problem counts.
F-015 defines list_parts — a backend function (and RPC) that scans parts/ folders.

These tests verify RPC registration, part discovery, maturity fields, and empty
workspace behavior.

Beginner concepts:
  - list_parts: returns [{part_id, name, maturity, open_problem_count}, ...].
  - maturity: draft → in_review → released lifecycle stage for a part.
  - spec.yaml: part metadata file; list_parts reads it to build panel rows.
"""

from __future__ import annotations

import importlib

import pytest
import yaml

from project.part_folder import SPEC_FILENAME, create_part_folder
from rpc_helpers import assert_rpc_method_registered, call_rpc, assert_rpc_success


def _list_parts_fn():
    """
    Import list_parts from project.parts_list (or legacy parts_catalog).

    Uses importlib so tests fail clearly if F-015 is not implemented yet.
    """
    try:
        mod = importlib.import_module("project.parts_list")
    except ImportError:
        mod = importlib.import_module("project.parts_catalog")
    fn = getattr(mod, "list_parts", None)
    if fn is None:
        pytest.fail("F-015 requires list_parts in project.parts_list or parts_catalog")
    return fn


def test_list_parts_rpc_registered(workspace):
    """list_parts must be registered as a JSON-RPC method."""
    assert_rpc_method_registered("list_parts", {"workspace_path": str(workspace)})


def test_list_parts_includes_valid_spec_folders(workspace):
    """Parts with valid spec.yaml folders must appear in the list."""
    create_part_folder(workspace, "mounting_plate")
    create_part_folder(workspace, "bracket")

    spec_path = workspace / "parts" / "mounting_plate" / SPEC_FILENAME
    spec = {
        "part_id": "mounting_plate",
        "name": "Mounting Plate",
        "maturity": "draft",
    }
    spec_path.write_text(yaml.safe_dump(spec, sort_keys=False), encoding="utf-8")

    list_parts = _list_parts_fn()
    parts = list_parts(workspace)
    ids = {p["part_id"] for p in parts}
    assert "mounting_plate" in ids
    assert "bracket" in ids


def test_list_parts_includes_maturity_and_problem_count(workspace):
    """Each part row must expose maturity and an integer open_problem_count."""
    create_part_folder(workspace, "mounting_plate")
    spec_path = workspace / "parts" / "mounting_plate" / SPEC_FILENAME
    spec_path.write_text(
        yaml.safe_dump(
            {"part_id": "mounting_plate", "name": "Plate", "maturity": "in_review"},
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    list_parts = _list_parts_fn()
    parts = list_parts(workspace)
    plate = next(p for p in parts if p["part_id"] == "mounting_plate")
    assert plate["maturity"] == "in_review"
    assert "open_problem_count" in plate
    assert isinstance(plate["open_problem_count"], int)


def test_list_parts_jsonrpc(workspace):
    """list_parts RPC should return parts including newly created ones."""
    create_part_folder(workspace, "widget")
    response = call_rpc("list_parts", {"workspace_path": str(workspace)})
    parts = assert_rpc_success(response)
    assert any(p["part_id"] == "widget" for p in parts)


def test_list_parts_empty_workspace(workspace):
    """A workspace with no parts should return an empty list."""
    list_parts = _list_parts_fn()
    parts = list_parts(workspace)
    assert parts == []


def test_list_parts_skips_invalid_spec(workspace):
    """
    Parts with broken specs may be skipped or listed depending on implementation.
    At minimum, list_parts must return a list without crashing.
    """
    create_part_folder(workspace, "broken")
    list_parts = _list_parts_fn()
    parts = list_parts(workspace)
    assert isinstance(parts, list)
