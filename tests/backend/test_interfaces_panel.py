"""Spec compliance tests for F-016 — Interfaces panel."""

from __future__ import annotations

import importlib

import pytest
import yaml

from rpc_helpers import assert_rpc_method_registered, call_rpc, assert_rpc_success
from spec_fixtures import write_linked_interface_specs, write_part_spec_with_interfaces


def _list_interfaces_fn():
    try:
        mod = importlib.import_module("project.interfaces_list")
    except ImportError:
        mod = importlib.import_module("project.interfaces_catalog")
    fn = getattr(mod, "list_interfaces", None)
    if fn is None:
        pytest.fail("F-016 requires list_interfaces in project.interfaces_list")
    return fn


def test_list_interfaces_rpc_registered(workspace):
    assert_rpc_method_registered("list_interfaces", {"workspace_path": str(workspace)})


def test_mounting_plate_interfaces_appear_when_defined(workspace):
    write_part_spec_with_interfaces(workspace, "mounting_plate")
    list_interfaces = _list_interfaces_fn()
    rows = list_interfaces(workspace)
    assert any(r["interface_id"] == "mount_a" and r["part_id"] == "mounting_plate" for r in rows)


def test_interface_status_open_when_not_linked(workspace):
    write_part_spec_with_interfaces(workspace, "mounting_plate")
    rows = _list_interfaces_fn()(workspace)
    row = next(r for r in rows if r["interface_id"] == "mount_a")
    assert row["status"] == "open"
    assert row.get("connected_part_id") in (None, "")


def test_interface_status_linked_when_connects_to_set(workspace):
    write_linked_interface_specs(workspace)
    plate_spec_path = workspace / "parts" / "mounting_plate" / "spec.yaml"
    spec = yaml.safe_load(plate_spec_path.read_text(encoding="utf-8"))
    spec["interfaces"][0]["connects_to"] = {"part_id": "bracket", "interface_id": "mount_b"}
    plate_spec_path.write_text(yaml.safe_dump(spec, sort_keys=False), encoding="utf-8")

    rows = _list_interfaces_fn()(workspace)
    linked = next(r for r in rows if r["interface_id"] == "mount_a")
    assert linked["status"] in ("linked", "verified")


def test_list_interfaces_jsonrpc(workspace):
    write_part_spec_with_interfaces(workspace, "mounting_plate")
    response = call_rpc("list_interfaces", {"workspace_path": str(workspace)})
    rows = assert_rpc_success(response)
    assert len(rows) >= 1


def test_list_interfaces_empty_when_none_defined(workspace):
    from project.part_folder import create_part_folder

    create_part_folder(workspace, "bare_part")
    rows = _list_interfaces_fn()(workspace)
    assert rows == []


def test_interface_row_fields_for_panel(workspace):
    write_part_spec_with_interfaces(workspace, "mounting_plate")
    row = _list_interfaces_fn()(workspace)[0]
    for key in ("part_id", "interface_id", "name", "type", "status"):
        assert key in row
