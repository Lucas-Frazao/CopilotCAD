"""Unit tests for part folder creation (F-002)."""

import json
from pathlib import Path

import yaml

from project.part_folder import (
    ASSUMPTIONS_FILENAME,
    HISTORY_FILENAME,
    SPEC_FILENAME,
    create_part_folder,
)
from project.workspace import create_workspace


def test_create_part_folder_creates_stub_files(tmp_path: Path):
    workspace = create_workspace(tmp_path / "proj", "proj")
    workspace_path = tmp_path / "proj"

    part_path = create_part_folder(workspace_path, "mounting_plate")

    assert part_path.is_dir()
    assert part_path.name == "mounting_plate"
    assert (part_path / SPEC_FILENAME).is_file()
    assert (part_path / ASSUMPTIONS_FILENAME).is_file()
    assert (part_path / HISTORY_FILENAME).is_file()

    spec = yaml.safe_load((part_path / SPEC_FILENAME).read_text(encoding="utf-8"))
    assumptions = yaml.safe_load(
        (part_path / ASSUMPTIONS_FILENAME).read_text(encoding="utf-8")
    )
    history = json.loads((part_path / HISTORY_FILENAME).read_text(encoding="utf-8"))

    assert spec == {}
    assert assumptions == {"assumptions": []}
    assert history == {"events": []}
