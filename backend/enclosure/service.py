"""
Generate / validate / export orchestration for the Evie enclosure connector.

In-process artifact store so a Grok bot can generate, then validate/export
the same solid without a workspace project.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from enclosure.builders import BuiltPart, build_approx_brick, build_part
from enclosure.features import NamedFeature
from enclosure.gates import run_gates
from enclosure.report import build_report
from enclosure.spec_loader import load_enclosure_spec
from engine import kernel_adapter

PUBLIC_PARTS = ("badge", "cover", "faceplate")
EXPORT_FORMATS = ("step", "stl", "iges")


@dataclass
class Artifact:
    artifact_id: str
    part: str
    shape: Any
    features: list[NamedFeature] = field(default_factory=list)


_STORE: dict[str, Artifact] = {}


def _put(built: BuiltPart) -> Artifact:
    artifact_id = uuid.uuid4().hex
    artifact = Artifact(
        artifact_id=artifact_id,
        part=built.part,
        shape=built.shape,
        features=list(built.features),
    )
    _STORE[artifact_id] = artifact
    return artifact


def get_artifact(artifact_id: str) -> Artifact:
    try:
        return _STORE[artifact_id]
    except KeyError as exc:
        raise KeyError(f"unknown artifact_id {artifact_id!r}") from exc


def generate_part(part: str, *, fill: float | None = None) -> dict[str, Any]:
    """Build a parametric part and stash it for later validate/export."""
    if part == "brick":
        built = build_approx_brick(0.80 if fill is None else fill)
    else:
        if part not in PUBLIC_PARTS and part != "brick":
            raise ValueError(f"unknown part {part!r}")
        built = build_part(part)
    artifact = _put(built)
    xmin, ymin, zmin, xmax, ymax, zmax = kernel_adapter.shape_bbox(built.shape)
    return {
        "ok": True,
        "part": built.part,
        "artifact_id": artifact.artifact_id,
        "extents": {
            "dx": xmax - xmin,
            "dy": ymax - ymin,
            "dz": zmax - zmin,
        },
        "feature_ids": [item.id for item in built.features],
        "ownership": "dogfood — not product print-GO",
    }


def validate_part(
    part: str | None = None,
    *,
    artifact_id: str | None = None,
    spec_path: str | Path | None = None,
    mate_artifact_id: str | None = None,
) -> dict[str, Any]:
    """Run hard gates against a stored or freshly generated solid."""
    if artifact_id:
        artifact = get_artifact(artifact_id)
        target_part = part or artifact.part
        shape = artifact.shape
        features = artifact.features
    else:
        if not part:
            raise ValueError("part or artifact_id is required")
        generated = generate_part(part)
        artifact = get_artifact(generated["artifact_id"])
        target_part = artifact.part
        shape = artifact.shape
        features = artifact.features

    spec = load_enclosure_spec(spec_path)
    gate_part = target_part if target_part in spec.get("parts", {}) else "faceplate"
    if target_part == "brick":
        gate_part = "faceplate"

    mate_features = None
    if mate_artifact_id:
        mate_features = get_artifact(mate_artifact_id).features

    measured, gates = run_gates(
        gate_part,
        spec,
        shape,
        features=features,
        mate_features=mate_features,
    )
    report = build_report(gate_part, spec, measured, gates, features)
    report["artifact_id"] = artifact.artifact_id
    report["generated_part"] = target_part
    return report


def export_part(
    format: str,
    dest: Path | str,
    *,
    part: str | None = None,
    artifact_id: str | None = None,
) -> dict[str, Any]:
    """Write STEP / STL / IGES. Dogfood artifact — not a product release."""
    fmt = format.lower().lstrip(".")
    if fmt not in EXPORT_FORMATS:
        raise ValueError(f"format must be one of {EXPORT_FORMATS}, got {format!r}")

    if artifact_id:
        artifact = get_artifact(artifact_id)
    else:
        if not part:
            raise ValueError("part or artifact_id is required")
        generated = generate_part(part)
        artifact = get_artifact(generated["artifact_id"])

    dest_path = Path(dest)
    if dest_path.suffix == "":
        dest_path = dest_path.with_suffix(f".{fmt}")
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    if fmt == "step":
        kernel_adapter.export_step(artifact.shape, dest_path)
    elif fmt == "stl":
        kernel_adapter.export_stl(artifact.shape, dest_path)
    else:
        kernel_adapter.export_iges(artifact.shape, dest_path)

    return {
        "ok": True,
        "part": artifact.part,
        "artifact_id": artifact.artifact_id,
        "format": fmt,
        "path": str(dest_path.resolve()),
        "bytes": dest_path.stat().st_size,
        "ownership": "dogfood — not product print-GO",
    }
