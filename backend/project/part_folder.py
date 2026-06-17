"""Read/write part folder artifacts."""

import json
from pathlib import Path

import yaml

PARTS_DIR = "parts"
SPEC_FILENAME = "spec.yaml"
ASSUMPTIONS_FILENAME = "assumptions.yaml"
HISTORY_FILENAME = "history.json"

DEFAULT_SPEC: dict = {}
DEFAULT_ASSUMPTIONS: dict = {"assumptions": []}
DEFAULT_HISTORY: dict = {"events": []}


def _part_dir(workspace: Path, part_id: str) -> Path:
    return workspace / PARTS_DIR / part_id


def create_part_folder(workspace: Path, part_id: str) -> Path:
    """Create parts/<part-id>/ with stub spec, assumptions, and history files."""
    part_path = _part_dir(workspace, part_id)
    part_path.mkdir(parents=True, exist_ok=True)

    spec_path = part_path / SPEC_FILENAME
    assumptions_path = part_path / ASSUMPTIONS_FILENAME
    history_path = part_path / HISTORY_FILENAME

    spec_path.write_text(
        yaml.safe_dump(DEFAULT_SPEC, sort_keys=False),
        encoding="utf-8",
    )
    assumptions_path.write_text(
        yaml.safe_dump(DEFAULT_ASSUMPTIONS, sort_keys=False),
        encoding="utf-8",
    )
    history_path.write_text(
        json.dumps(DEFAULT_HISTORY, indent=2) + "\n",
        encoding="utf-8",
    )

    return part_path
