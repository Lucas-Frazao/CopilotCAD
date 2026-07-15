"""
conftest.py — Shared pytest fixtures for backend tests
=======================================================

Pytest automatically discovers and loads this file before running any test in
this folder. Fixtures defined here are reusable setup helpers: they create
temporary workspaces, sample part folders, or Intent IR dictionaries that many
tests share.

Related feature specs: F-010+ backend compliance tests depend on these fixtures.

Beginner concepts:
  - Fixture: a function pytest calls to prepare test data; tests request it by
    naming the fixture as a parameter.
  - tmp_path: a pytest-provided temporary directory, deleted after each test.
  - Workspace: a CopilotCAD project root with docs/, parts/, assemblies/, exports/.
  - Intent IR: a JSON-like dict describing what the user wants the CAD engine to build.
"""

from __future__ import annotations  # Lets us use Path in type hints without quotes

from pathlib import Path  # Cross-platform file and folder paths

import pytest  # The test framework that discovers and runs these tests

# Backend modules that create on-disk project structure
from project.part_folder import create_part_folder
from project.workspace import create_workspace

# Reuse the golden mounting-plate IR defined in test_intent_ir_validation.py
from test_intent_ir_validation import mounting_plate_ir


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    """
    Provide a blank CopilotCAD workspace with standard top-level folders.

    Any test that lists `workspace` as a parameter receives a fresh project
    directory under pytest's temporary folder.
    """
    root = tmp_path / "proj"
    create_workspace(root, "proj")  # Writes manifest + docs/parts/assemblies/exports
    return root


@pytest.fixture
def workspace_with_mounting_plate(workspace: Path) -> Path:
    """
    Same as `workspace`, but with a mounting_plate part folder already scaffolded.

    Depends on the `workspace` fixture above — pytest wires that automatically.
    """
    create_part_folder(workspace, "mounting_plate")
    return workspace


@pytest.fixture
def mounting_plate_ir_dict() -> dict:
    """Return the canonical mounting-plate Intent IR as a plain Python dictionary."""
    return mounting_plate_ir()
