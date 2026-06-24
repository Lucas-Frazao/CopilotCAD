"""Reusable IR and workspace fixtures for F-010+ spec compliance tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from project.part_folder import ASSUMPTIONS_FILENAME, HISTORY_FILENAME, SPEC_FILENAME
from project.workspace import create_workspace
from project.part_folder import create_part_folder


def assembly_create_ir(assembly_id: str = "demo_asm") -> dict[str, Any]:
    return {
        "type": "assembly_create",
        "prompt": "Create assembly with mounting plate and bracket",
        "summary": "Two-part demo assembly",
        "target": {"assembly_id": assembly_id},
        "context": {"active_part_id": None},
        "questions": [],
        "assumptions": [],
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
        "links": {"interface_refs": ["mount_a", "mount_b"]},
    }


def write_part_spec_with_interfaces(workspace: Path, part_id: str) -> None:
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
                "connects_to": None,
            }
        ],
    }
    spec_path.write_text(yaml.safe_dump(spec, sort_keys=False), encoding="utf-8")


def write_linked_interface_specs(workspace: Path) -> tuple[str, str]:
    """Two parts with interfaces that can be linked by F-021."""
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


def write_assumptions_yaml(workspace: Path, part_id: str, assumptions: list[dict]) -> None:
    path = workspace / "parts" / part_id / ASSUMPTIONS_FILENAME
    path.write_text(
        yaml.safe_dump({"assumptions": assumptions}, sort_keys=False),
        encoding="utf-8",
    )


def read_history_events(workspace: Path, part_id: str) -> list[dict]:
    import json

    path = workspace / "parts" / part_id / HISTORY_FILENAME
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("events", [])


def make_workspace_with_two_parts(tmp_path: Path) -> Path:
    workspace = tmp_path / "asm_proj"
    create_workspace(workspace, "asm_proj")
    write_part_spec_with_interfaces(workspace, "mounting_plate")
    create_part_folder(workspace, "bracket")
    return workspace
