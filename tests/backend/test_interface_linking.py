"""
test_interface_linking.py — Interface linking in assemblies tests (F-021)
=========================================================================

When assembly mates are applied, F-021 updates connects_to fields in both parts'
spec.yaml files so the Interfaces panel shows linked status.

These tests verify mate-driven linking, idempotency, conflict detection, and
interface_refs pairing on mate steps.

Beginner concepts:
  - connects_to: {part_id, interface_id} cross-reference in spec.yaml.
  - apply_interface_links_for_mate: writes connects_to after a mate executes.
  - interface_conflict: problem raised when linked interfaces have mismatched specs.
"""

from __future__ import annotations

import importlib

import pytest
import yaml

from ir.validator import validate_intent_ir
from problems.engine import evaluate_problems
from spec_fixtures import mate_coincident_ir, write_linked_interface_specs


def _linking_module():
    """Import assembly.interface_linking or fail with a clear F-021 pending message."""
    try:
        return importlib.import_module("assembly.interface_linking")
    except ImportError as exc:
        pytest.fail(f"F-021 requires backend/assembly/interface_linking.py: {exc}")


def test_mate_updates_connects_to_on_both_specs(workspace):
    """
    After apply_interface_links_for_mate, both plate and bracket spec.yaml
    must have connects_to set on their respective interfaces.
    """
    write_linked_interface_specs(workspace)
    linking = _linking_module()
    apply_links = getattr(linking, "apply_interface_links_for_mate", None)
    assert apply_links is not None

    intent = validate_intent_ir(mate_coincident_ir())
    apply_links(workspace, intent)

    plate_spec = yaml.safe_load(
        (workspace / "parts" / "mounting_plate" / "spec.yaml").read_text(encoding="utf-8")
    )
    bracket_spec = yaml.safe_load(
        (workspace / "parts" / "bracket" / "spec.yaml").read_text(encoding="utf-8")
    )

    plate_conn = plate_spec["interfaces"][0].get("connects_to")
    bracket_conn = bracket_spec["interfaces"][0].get("connects_to")
    assert plate_conn is not None
    assert bracket_conn is not None
    assert plate_conn.get("part_id") == "bracket" or plate_conn.get("interface_id") == "mount_b"


def test_repeated_mate_is_idempotent(workspace):
    """
    Applying the same mate twice must not duplicate connects_to entries.
    """
    write_linked_interface_specs(workspace)
    linking = _linking_module()
    apply_links = linking.apply_interface_links_for_mate
    intent = validate_intent_ir(mate_coincident_ir())
    apply_links(workspace, intent)
    apply_links(workspace, intent)

    plate_spec = yaml.safe_load(
        (workspace / "parts" / "mounting_plate" / "spec.yaml").read_text(encoding="utf-8")
    )
    connects = plate_spec["interfaces"][0]["connects_to"]
    if isinstance(connects, list):
        assert len(connects) == 1


def test_mismatched_interface_triggers_conflict_problem(workspace):
    """
    Conflicting bolt_pattern values on linked interfaces must surface
    an interface_conflict problem.
    """
    write_linked_interface_specs(workspace)
    plate_path = workspace / "parts" / "mounting_plate" / "spec.yaml"
    spec = yaml.safe_load(plate_path.read_text(encoding="utf-8"))
    spec["interfaces"][0]["bolt_pattern"] = "M3"
    plate_path.write_text(yaml.safe_dump(spec, sort_keys=False), encoding="utf-8")

    bracket_path = workspace / "parts" / "bracket" / "spec.yaml"
    bspec = yaml.safe_load(bracket_path.read_text(encoding="utf-8"))
    bspec["interfaces"][0]["bolt_pattern"] = "M5"
    bracket_path.write_text(yaml.safe_dump(bspec, sort_keys=False), encoding="utf-8")

    linking = _linking_module()
    compare = getattr(linking, "evaluate_interface_conflicts", None)
    assert compare is not None
    problems = compare(workspace)
    assert any(p.type == "interface_conflict" for p in problems)


def test_interface_refs_on_mate_step_used_for_pairing(workspace):
    """
    resolve_interface_pair must use links.interface_refs from the mate IR
    to identify which interfaces to connect (mount_a and mount_b).
    """
    linking = _linking_module()
    resolve = getattr(linking, "resolve_interface_pair", None)
    assert resolve is not None
    intent = validate_intent_ir(mate_coincident_ir())
    pair = resolve(intent)
    assert pair is not None
    assert "mount_a" in str(pair) or "mount_b" in str(pair)
