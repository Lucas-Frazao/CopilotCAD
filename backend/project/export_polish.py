"""STEP/IGES export helpers (F-024)."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from project.geometry_cache import load_part_geometry
from project.history import append_export_history

ExportFormat = Literal["step", "iges"]


class ExportError(Exception):
    """Raised when export cannot proceed."""


def _exports_dir(workspace: Path) -> Path:
    path = workspace / "exports"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _require_geometry(workspace: Path, part_id: str):
    shape = load_part_geometry(workspace, part_id)
    if shape is None:
        raise ExportError(
            f"No geometry cached for part '{part_id}' — model this part first."
        )
    return shape


def export_part(
    workspace: Path,
    part_id: str,
    *,
    format: ExportFormat = "step",
) -> Path:
    shape = _require_geometry(workspace, part_id)
    exports = _exports_dir(workspace)

    if format == "step":
        from kernel.occt_bridge import export_step

        out_path = exports / f"{part_id}.step"
        export_step(shape, out_path)
        return out_path

    from kernel.occt_bridge import export_iges

    out_path = exports / f"{part_id}.iges"
    export_iges(shape, out_path)
    return out_path


def export_assembly(
    workspace: Path,
    assembly_id: str,
    *,
    format: ExportFormat = "step",
) -> Path:
    from project.assembly_folder import read_assembly

    assembly = read_assembly(workspace, assembly_id)
    instances = assembly.get("instances", [])
    if not instances:
        raise ExportError(f"assembly '{assembly_id}' has no instances to export")

    primary_part = instances[0]["part_id"]
    shape = _require_geometry(workspace, primary_part)
    exports = _exports_dir(workspace)

    if format == "step":
        from kernel.occt_bridge import export_step

        out_path = exports / f"{assembly_id}.step"
        export_step(shape, out_path)
        return out_path

    from kernel.occt_bridge import export_iges

    out_path = exports / f"{assembly_id}.iges"
    export_iges(shape, out_path)
    return out_path


def export_part_with_history(
    workspace: Path,
    part_id: str,
    *,
    format: ExportFormat = "step",
) -> Path:
    out_path = export_part(workspace, part_id, format=format)
    append_export_history(workspace, part_id, out_path, format)
    return out_path