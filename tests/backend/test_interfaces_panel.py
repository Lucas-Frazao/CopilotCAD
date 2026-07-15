"""
test_interfaces_panel.py — Interfaces panel spec compliance tests (F-016)
=========================================================================

Interfaces describe connection points between parts (mounting faces, ports, etc.).
F-016 defines list_interfaces — a backend scan of all part spec.yaml files that
returns rows the Interfaces panel can render with status (open vs linked).

Beginner concepts:
  - Interface: defined in spec.yaml under interfaces[] with id, name, type.
  - connects_to: when set, links this interface to another part's interface.
  - status: "open" (unlinked) or "linked"/"verified" (connected).
"""

from __future__ import annotations

import importlib

import pytest
import yaml

from rpc_helpers import assert_rpc_method_registered, call_rpc, assert_rpc_success
from spec_fixtures import write_linked_interface_specs, write_part_spec_with_interfaces


def _list_interfaces_fn():
    """
    Import list_interfaces from project.interfaces_list (or legacy catalog).

    Tries interfaces_list first, falls back to interfaces_catalog.
    """
    try:
        mod = importlib.import_module("project.interfaces_list")
    except ImportError:
        mod = importlib.import_module("project.interfaces_catalog")
    fn = getattr(mod, "list_interfaces", None)
    if fn is None:
        pytest.fail("F-016 requires list_interfaces in project.interfaces_list")
    return fn


def test_list_interfaces_rpc_registered(workspace):
    """list_interfaces must be registered as a JSON-RPC method."""
    assert_rpc_method_registered("list_interfaces", {"workspace_path": str(workspace)})


def test_mounting_plate_interfaces_appear_when_defined(workspace):
    """An interface defined in spec.yaml must appear in list_interfaces output."""
    write_part_spec_with_interfaces(workspace, "mounting_plate")
    list_interfaces = _list_interfaces_fn()
    rows = list_interfaces(workspace)
    assert any(r["interface_id"] == "mount_a" and r["part_id"] == "mounting_plate" for r in rows)


def test_interface_status_open_when_not_linked(workspace):
    """Unlinked interfaces should have status 'open' and no connected_part_id."""
    write_part_spec_with_interfaces(workspace, "mounting_plate")
    rows = _list_interfaces_fn()(workspace)
    row = next(r for r in rows if r["interface_id"] == "mount_a")
    assert row["status"] == "open"
    assert row.get("connected_part_id") in (None, "")


def test_interface_status_linked_when_connects_to_set(workspace):
    """
    Manually setting connects_to in spec.yaml should flip status to linked.
    """
    write_linked_interface_specs(workspace)
    plate_spec_path = workspace / "parts" / "mounting_plate" / "spec.yaml"
    spec = yaml.safe_load(plate_spec_path.read_text(encoding="utf-8"))
    spec["interfaces"][0]["connects_to"] = {"part_id": "bracket", "interface_id": "mount_b"}
    plate_spec_path.write_text(yaml.safe_dump(spec, sort_keys=False), encoding="utf-8")

    rows = _list_interfaces_fn()(workspace)
    linked = next(r for r in rows if r["interface_id"] == "mount_a")
    assert linked["status"] in ("linked", "verified")


def test_list_interfaces_jsonrpc(workspace):
    """list_interfaces RPC should return at least one row when interfaces exist."""
    write_part_spec_with_interfaces(workspace, "mounting_plate")
    response = call_rpc("list_interfaces", {"workspace_path": str(workspace)})
    rows = assert_rpc_success(response)
    assert len(rows) >= 1


def test_list_interfaces_empty_when_none_defined(workspace):
    """A part with no interfaces defined should contribute zero rows."""
    from project.part_folder import create_part_folder

    create_part_folder(workspace, "bare_part")
    rows = _list_interfaces_fn()(workspace)
    assert rows == []


def test_interface_row_fields_for_panel(workspace):
    """Each interface row must include fields the panel UI needs to render."""
    write_part_spec_with_interfaces(workspace, "mounting_plate")
    row = _list_interfaces_fn()(workspace)[0]
    for key in ("part_id", "interface_id", "name", "type", "status"):
        assert key in row
