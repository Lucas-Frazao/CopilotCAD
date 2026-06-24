"""Shared pytest fixtures for backend spec compliance tests (F-010+)."""

from __future__ import annotations

from pathlib import Path

import pytest

from project.part_folder import create_part_folder
from project.workspace import create_workspace
from test_intent_ir_validation import mounting_plate_ir


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    """Blank CopilotCAD workspace with standard folders."""
    root = tmp_path / "proj"
    create_workspace(root, "proj")
    return root


@pytest.fixture
def workspace_with_mounting_plate(workspace: Path) -> Path:
    create_part_folder(workspace, "mounting_plate")
    return workspace


@pytest.fixture
def mounting_plate_ir_dict() -> dict:
    return mounting_plate_ir()
