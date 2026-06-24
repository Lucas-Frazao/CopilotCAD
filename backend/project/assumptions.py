"""Assumption management for parts (F-023)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from project.part_folder import ASSUMPTIONS_FILENAME

VALID_STATUSES = frozenset({"proposed", "confirmed", "rejected"})


class AssumptionError(Exception):
    """Raised when assumption updates are invalid."""


def _assumptions_path(workspace: Path, part_id: str) -> Path:
    return workspace / "parts" / part_id / ASSUMPTIONS_FILENAME


def _load_assumptions(workspace: Path, part_id: str) -> dict[str, Any]:
    path = _assumptions_path(workspace, part_id)
    if not path.is_file():
        return {"assumptions": []}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {"assumptions": []}
    if not isinstance(data.get("assumptions"), list):
        data["assumptions"] = []
    return data


def update_assumption(
    workspace: Path,
    part_id: str,
    assumption_id: str,
    status: str,
    text: str | None = None,
) -> dict[str, Any]:
    if status not in VALID_STATUSES:
        raise AssumptionError(f"invalid assumption status: {status!r}")

    data = _load_assumptions(workspace, part_id)
    assumptions = data["assumptions"]
    target = next((item for item in assumptions if item.get("id") == assumption_id), None)
    if target is None:
        raise AssumptionError(f"Unknown assumption_id: {assumption_id}")

    target["status"] = status
    if text is not None:
        target["text"] = text

    path = _assumptions_path(workspace, part_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return target