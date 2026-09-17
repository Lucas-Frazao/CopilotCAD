"""Load the Evie enclosure machine-readable spec (YAML or JSON)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

SPEC_RELATIVE = Path("specs/evie/evie_enclosure_v3_spec.yaml")


def repo_root() -> Path:
    """Walk parents until AGENTS.md is found (repo root)."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "AGENTS.md").is_file():
            return parent
    raise FileNotFoundError("Could not locate CopilotCAD repo root (missing AGENTS.md)")


def default_spec_path() -> Path:
    return repo_root() / SPEC_RELATIVE


def load_enclosure_spec(path: Path | str | None = None) -> dict[str, Any]:
    """
    Load the Evie v3 enclosure spec.

    Accepts ``.yaml`` / ``.yml`` / ``.json``. Defaults to the checked-in SoT.
    """
    spec_path = Path(path) if path is not None else default_spec_path()
    if not spec_path.is_file():
        raise FileNotFoundError(f"Enclosure spec not found: {spec_path}")

    text = spec_path.read_text(encoding="utf-8")
    suffix = spec_path.suffix.lower()
    if suffix == ".json":
        loaded = json.loads(text)
    else:
        loaded = yaml.safe_load(text)

    if not isinstance(loaded, dict):
        raise TypeError(f"Enclosure spec must be a mapping, got {type(loaded).__name__}")
    return loaded
