"""
spec_fixtures.py — Reusable IR and workspace fixtures
======================================================

Factory functions that build sample Intent IR documents and on-disk workspace
state for assembly, interface, assumption, and history tests.

Used by: F-010+ spec compliance tests that need realistic project layouts without
copy-pasting the same setup code into every file.

Beginner concepts:
  - Intent IR: structured JSON describing CAD operations (sketch, extrude, mate, etc.).
  - Part folder: parts/<part_id>/ with spec.yaml, assumptions.yaml, history.json.
  - Assembly: a YAML file listing part instances placed together in 3D space.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml  # Read/write YAML part specs and assembly files

# Constants for standard filenames inside each part folder
from project.part_folder import ASSUMPTIONS_FILENAME, HISTORY_FILENAME, SPEC_FILENAME
from project.workspace import create_workspace
from project.part_folder import create_part_folder


def assembly_create_ir(assembly_id: str = "demo_asm") -> dict[str, Any]:
    """
    Build a minimal assembly_create Intent IR with two part instances.

    Tests use this to verify assembly scaffolding without hand-writing JSON each time.
    """
    return {
        "type": "assembly_create",
        "prompt": "Create assembly with mounting plate and bracket",
        "summary": "Two-part demo assembly",
        "target": {"assembly_id": assembly_id},
        "context": {"active_part_id": None},
        "questions": [],
        "assumptions": [],
        # constraints.instances lists which parts appear in the assembly
        "constraints": {
            "instances": [
                {"instance_id": "inst_plate", "part_id": "mounting_plate"},
                {"instance_id": "inst_bracket", "part_id": "bracket"},
            ]
        },
        "steps": [],
        "links": {"spec_refs": [], "requirement_refs": [], "architecture_refs": []},
    }


def mate_coincident_ir() -> dict[str, Any]:
    """
    Build an IR with one mate_coincident step linking two assembly instances.

    Used by F-019 (mates) and F-021 (interface linking) tests.
    """
    return {
        "type": "assembly_create",
        "prompt": "Mate plate to bracket",
        "summary": "Apply coincident mate",
        "target": {"assembly_id": "demo_asm"},
        "steps": [
            {
                "id": "m1",
                "op": "mate_coincident",
                "params": {
                    "instance_a": "inst_plate",
                    "instance_b": "inst_bracket",
                    "face_a": "face_top",
                    "face_b": "face_bottom",
                },
            }
        ],
        # links.interface_refs tell the linker which interfaces to connect
        "links": {"interface_refs": ["mount_a", "mount_b"]},
    }


def write_part_spec_with_interfaces(workspace: Path, part_id: str) -> None:
    """
    Create a part folder and write a spec.yaml with one mechanical interface.

    Interfaces describe connection points between parts (e.g. a mounting face).
    """
    create_part_folder(workspace, part_id)
    spec_path = workspace / "parts" / part_id / SPEC_FILENAME
    spec = {
        "part_id": part_id,
        "name": part_id.replace("_", " ").title(),
        "maturity": "draft",
        "interfaces": [
            {
                "id": "mount_a",
                "name": "Mount face",
                "type": "mechanical",
                "connects_to": None,  # Not linked to another part yet
            }
        ],
    }
    spec_path.write_text(yaml.safe_dump(spec, sort_keys=False), encoding="utf-8")


def write_linked_interface_specs(workspace: Path) -> tuple[str, str]:
    """
    Create two parts with interfaces that F-021 can link together.

    Returns (plate_id, bracket_id) so tests can assert on both part names.
    """
    plate_id, bracket_id = "mounting_plate", "bracket"
    write_part_spec_with_interfaces(workspace, plate_id)
    create_part_folder(workspace, bracket_id)
    bracket_spec = {
        "part_id": bracket_id,
        "name": "Bracket",
        "maturity": "draft",
        "interfaces": [
            {
                "id": "mount_b",
                "name": "Bracket mount",
                "type": "mechanical",
                "connects_to": None,
            }
        ],
    }
    spec_path = workspace / "parts" / bracket_id / SPEC_FILENAME
    spec_path.write_text(yaml.safe_dump(bracket_spec, sort_keys=False), encoding="utf-8")
    return plate_id, bracket_id


def write_assumptions_yaml(
    workspace: Path,
    part_id: str,
    assumptions: list[dict],
) -> None:
    """Write assumptions.yaml for a part — AI guesses the user must confirm or edit."""
    path = workspace / "parts" / part_id / ASSUMPTIONS_FILENAME
    path.write_text(
        yaml.safe_dump({"assumptions": assumptions}, sort_keys=False),
        encoding="utf-8",
    )


def read_history_events(workspace: Path, part_id: str) -> list[dict]:
    """Load the events array from a part's history.json audit log."""
    import json

    path = workspace / "parts" / part_id / HISTORY_FILENAME
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("events", [])


def make_workspace_with_two_parts(tmp_path: Path) -> Path:
    """
    Create a workspace with mounting_plate (with interface) and a bare bracket folder.

    Convenience setup for assembly mesh and mate tests.
    """
    workspace = tmp_path / "asm_proj"
    create_workspace(workspace, "asm_proj")
    write_part_spec_with_interfaces(workspace, "mounting_plate")
    create_part_folder(workspace, "bracket")
    return workspace
