"""Interfaces panel listing (F-016)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from project.part_folder import PARTS_DIR, SPEC_FILENAME


def _interface_status(connects_to: Any) -> str:
    if connects_to in (None, "", {}):
        return "open"
    if isinstance(connects_to, dict) and connects_to.get("part_id"):
        return "linked"
    if isinstance(connects_to, list) and connects_to:
        return "linked"
    return "open"


def _connected_part_id(connects_to: Any) -> str | None:
    if isinstance(connects_to, dict):
        return connects_to.get("part_id")
    return None


def list_interfaces(workspace: Path) -> list[dict[str, Any]]:
    """Return interface rows across all parts in the workspace."""
    parts_dir = workspace / PARTS_DIR
    if not parts_dir.is_dir():
        return []

    rows: list[dict[str, Any]] = []
    for part_dir in sorted(parts_dir.iterdir()):
        if not part_dir.is_dir():
            continue

        spec_path = part_dir / SPEC_FILENAME
        if not spec_path.is_file():
            continue

        try:
            spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            continue
        if not isinstance(spec, dict):
            continue

        part_id = spec.get("part_id", part_dir.name)
        interfaces = spec.get("interfaces", [])
        if not isinstance(interfaces, list):
            continue

        for interface in interfaces:
            if not isinstance(interface, dict):
                continue
            connects_to = interface.get("connects_to")
            rows.append(
                {
                    "part_id": part_id,
                    "interface_id": interface.get("id", ""),
                    "name": interface.get("name", interface.get("id", "")),
                    "type": interface.get("type", "mechanical"),
                    "status": _interface_status(connects_to),
                    "connected_part_id": _connected_part_id(connects_to),
                }
            )

    return rows