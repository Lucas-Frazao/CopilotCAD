"""
STEP Export — Thin OCCT Bridge Wrapper (F-004)
=============================================

WHAT THIS FILE DOES
-------------------
Single-function helper to write a TopoDS shape to a STEP file on disk.
Delegates all OCCT work to kernel.occt_bridge.export_step.
"""

from pathlib import Path
from typing import Any, Union

PathLike = Union[str, Path]


def export_step_file(shape: Any, path: PathLike) -> None:
    """Write a TopoDS shape to a STEP file."""
    from kernel.occt_bridge import export_step

    export_step(shape, path)
