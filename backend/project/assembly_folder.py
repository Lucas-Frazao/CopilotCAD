"""Assembly YAML read/write and assembly_create scaffolding (F-018)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from project.part_folder import create_part_folder

ASSEMBLIES_DIR = "assemblies"


class AssemblyError(Exception):
    """Raised when assembly operations fail."""


def _assembly_path(workspace: Path, assembly_id: str) -> Path:
    return workspace / ASSEMBLIES_DIR / f"{assembly_id}.yaml"


def create_assembly(workspace: Path, assembly_id: str, data: dict[str, Any]) -> Path:
    """Write assemblies/<id>.yaml."""
    path = _assembly_path(workspace, assembly_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "id": data.get("id", assembly_id),
        "name": data.get("name", assembly_id.replace("_", " ").title()),
        "instances": data.get("instances", []),
    }
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


def read_assembly(workspace: Path, assembly_id: str) -> dict[str, Any]:
    path = _assembly_path(workspace, assembly_id)
    if not path.is_file():
        raise AssemblyError(f"assembly not found: {assembly_id}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssemblyError(f"invalid assembly file: {assembly_id}")
    return data


def _instances_from_ir(ir_data: dict[str, Any]) -> list[dict[str, str]]:
    constraints = ir_data.get("constraints", {})
    if not isinstance(constraints, dict):
        return []

    instances = constraints.get("instances")
    if isinstance(instances, list) and instances:
        return [
            {
                "instance_id": item["instance_id"],
                "part_id": item["part_id"],
            }
            for item in instances
            if isinstance(item, dict) and "instance_id" in item and "part_id" in item
        ]

    dimensions = constraints.get("dimensions", {})
    if isinstance(dimensions, dict):
        nested = dimensions.get("instances")
        if isinstance(nested, list):
            return [
                {
                    "instance_id": item["instance_id"],
                    "part_id": item["part_id"],
                }
                for item in nested
                if isinstance(item, dict) and "instance_id" in item and "part_id" in item
            ]
    return []


def execute_assembly_create(workspace: Path, ir_data: dict[str, Any]) -> dict[str, Any]:
    """Scaffold part folders and assembly YAML from an assembly_create IR."""
    target = ir_data.get("target", {})
    assembly_id = target.get("assembly_id") if isinstance(target, dict) else None
    if not assembly_id:
        raise AssemblyError("assembly_create requires target.assembly_id")

    instances = _instances_from_ir(ir_data)
    for instance in instances:
        create_part_folder(workspace, instance["part_id"])

    create_assembly(
        workspace,
        assembly_id,
        {
            "id": assembly_id,
            "name": ir_data.get("summary", assembly_id),
            "instances": instances,
        },
    )
    return {"assembly_id": assembly_id, "instances": instances}