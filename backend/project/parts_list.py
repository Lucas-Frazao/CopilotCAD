"""
Parts Panel Listing — parts/<id>/ Rows (F-015)
==============================================

WHAT THIS FILE DOES
-------------------
Scans the workspace parts/ directory and returns table rows for the Parts panel
in the Electron UI.

ROW FIELDS
----------
part_id, name, maturity, open_problem_count (0 in MVP — filled by frontend later)

SKIPS
-----
Folders without a readable spec.yaml are omitted.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from project.part_folder import PARTS_DIR, SPEC_FILENAME


def _load_spec(spec_path: Path) -> dict[str, Any] | None:
    if not spec_path.is_file():
        return None
    try:
        data = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return None
    return data if isinstance(data, dict) else None


def list_parts(workspace: Path) -> list[dict[str, Any]]:
    """Return part rows for the parts panel."""
    parts_dir = workspace / PARTS_DIR
    if not parts_dir.is_dir():
        return []

    rows: list[dict[str, Any]] = []
    for part_dir in sorted(parts_dir.iterdir()):
        if not part_dir.is_dir():
            continue

        part_id = part_dir.name
        spec = _load_spec(part_dir / SPEC_FILENAME)
        if spec is None:
            continue

        rows.append(
            {
                "part_id": spec.get("part_id", part_id),
                "name": spec.get("name", part_id.replace("_", " ").title()),
                "maturity": spec.get("maturity", "draft"),
                "open_problem_count": 0,
            }
        )

    return rows
