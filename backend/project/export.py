"""STEP export via OCCT bridge (F-004)."""

from pathlib import Path
from typing import Any, Union

PathLike = Union[str, Path]


def export_step_file(shape: Any, path: PathLike) -> None:
    """Write a TopoDS shape to a STEP file."""
    from kernel.occt_bridge import export_step

    export_step(shape, path)
