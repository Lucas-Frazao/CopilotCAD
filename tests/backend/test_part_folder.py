"""
test_part_folder.py — Part folder creation unit tests (F-002)
=============================================================

When a user creates a new part, the backend scaffolds a folder under parts/
with stub files: spec.yaml, assumptions.yaml, and history.json.

F-002 defines this on-disk layout. These tests verify the stubs are created
with the expected empty defaults.

Beginner concepts:
  - Part folder: parts/<part_id>/ holding all metadata for one CAD part.
  - Stub files: placeholder files written immediately; content fills in later.
"""

import json  # Parse history.json
from pathlib import Path

import yaml  # Parse spec.yaml and assumptions.yaml

from project.part_folder import (
    ASSUMPTIONS_FILENAME,
    HISTORY_FILENAME,
    SPEC_FILENAME,
    create_part_folder,
)
from project.workspace import create_workspace


def test_create_part_folder_creates_stub_files(tmp_path: Path):
    """
    create_part_folder must create the directory and three stub artifact files.

    tmp_path is pytest's temporary directory — safe to write into during tests.
    """
    workspace = create_workspace(tmp_path / "proj", "proj")
    workspace_path = tmp_path / "proj"

    part_path = create_part_folder(workspace_path, "mounting_plate")

    # Folder exists with the correct name
    assert part_path.is_dir()
    assert part_path.name == "mounting_plate"

    # All three standard artifact files are present
    assert (part_path / SPEC_FILENAME).is_file()
    assert (part_path / ASSUMPTIONS_FILENAME).is_file()
    assert (part_path / HISTORY_FILENAME).is_file()

    # Read each file and verify the empty-default structure
    spec = yaml.safe_load((part_path / SPEC_FILENAME).read_text(encoding="utf-8"))
    assumptions = yaml.safe_load(
        (part_path / ASSUMPTIONS_FILENAME).read_text(encoding="utf-8")
    )
    history = json.loads((part_path / HISTORY_FILENAME).read_text(encoding="utf-8"))

    assert spec == {}
    assert assumptions == {"assumptions": []}
    assert history == {"events": []}
